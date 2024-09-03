
import time
import importlib
import datetime
import json
import os
import pytz


from pyflink.common import WatermarkStrategy
from pyflink.common.serialization import DeserializationSchema, SerializationSchema
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import DeliveryGuarantee
from pyflink.datastream.connectors.kafka import KafkaSource, \
    KafkaSink, KafkaRecordSerializationSchema, KafkaOffsetsInitializer
from pyflink.java_gateway import get_gateway



#import conversation_engines.call_center.conversation_manager as conversation_manager

def current_ts():
    now = datetime.datetime.now(pytz.timezone('America/Toronto'))
    return now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]


class BinaryDeserializationSchema(DeserializationSchema):
    def deserialize(self, message: bytes):
        # Directly return the binary message
        return message

    def is_end_of_stream(self, next_element):
        # End of stream is not defined for continuous message consumption
        return False

    def get_produced_type(self):
        # Return the type information for the deserialized data
        return Types.PRIMITIVE_ARRAY(Types.BYTE())

class PassthroughSerializationSchema(SerializationSchema):
    def serialize(self, value):
        return str(value)


def initial_greeting(caller_id, conversation_id, conversation_module, conversation_context):
    t1 = time.time()
    print(f"{current_ts()}: 0.000s received call {conversation_id} from {caller_id}: generating initial greeting")
    # {"text": greeting_text, "audio": bytes}
    convo_context = json.loads(conversation_context)
    conversation_manager = load_conversation_manager_module(conversation_module)
    conversation_manager.initialize_conversation(caller_id, conversation_id, convo_context)
    greeting = conversation_manager.get_initial_greeting(caller_id, conversation_id)
 
    return format_response_for_serialization(conversation_id, greeting)

def next_response(caller_id, conversation_id, conversation_module, request_phrase):
    t1 = time.time()
    print(f"{current_ts()}: 0.0s conversation {conversation_id} received phrase from {caller_id}, generating response for: {request_phrase}")
    conversation_manager = load_conversation_manager_module(conversation_module)
    response = conversation_manager.get_response(caller_id, conversation_id, request_phrase)
    print(f"{current_ts()}: {time.time() - t1}s response generated: {response}")

    return format_response_for_serialization(conversation_id, response)

def load_conversation_manager_module(conversation_module):
    return importlib.import_module(conversation_module)


def format_response_for_serialization(conversation_id, response):
    response_text = response.get('text', '') if response is not None and response and response['text'] else []
    key = json.dumps({'conversationId': conversation_id})
    return json.dumps({'key': key, 'value': response_text})


if __name__ == "__main__":
    # Kafka configuration
    conversations_topic = os.getenv("PHYSICIAN_TRANSCRIPT_TOPIC") 
    output_topic =  os.getenv("PATIENT_TRANSCRIPT_OUTPUT_TOPIC")
    bootstrap_servers =  os.getenv("KAFKA_BOOTSTRAP_SERVER") 
    group_id =  os.getenv("CONVERSATION_ENGINE_GROUP_ID")

    env = StreamExecutionEnvironment.get_execution_environment()
    print('Flink parallelism:', env.get_parallelism())

    conversation_module_default = "patient_endpoint"
   
    jar_path = os.getenv("JAR_DEPENDENCY_PATH")
    env.add_jars(f"file://{jar_path}")
    print(f'added jar {jar_path}')

    gate_way = get_gateway()

    j_byte_array_deserialization_schema = gate_way \
        .jvm.studio.goodlabs.monkeyjacket.KafkaMapByteArrayDeserializationSchema()
    j_json_key_serilization_schema = gate_way \
        .jvm.studio.goodlabs.monkeyjacket.KafkaKeyJsonSerializationSchema()
    j_json_value_serialization_schema = gate_way \
        .jvm.studio.goodlabs.monkeyjacket.KafkaValueJsonSerializationSchema()
    
    

    kafka_user = os.environ["KAFKA_CHAT_USER"]
    kafka_password = os.environ["KAFKA_CHAT_PASSWORD"]

    conversations_kafka_source = KafkaSource.builder() \
        .set_bootstrap_servers(bootstrap_servers) \
        .set_topics(conversations_topic) \
        .set_group_id(group_id) \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_deserializer(BinaryDeserializationSchema(j_deserialization_schema=j_byte_array_deserialization_schema)) \
        .set_property('security.protocol', 'SASL_SSL') \
        .set_property('sasl.mechanism', 'PLAIN') \
        .set_property('sasl.jaas.config',
                      f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{kafka_user}" password="{kafka_password}";') \
        .set_property('ssl.ca.location', 'ISRG Root X1.crt') \
        .build()
    

    key_value_kafka_serialization_schema = KafkaRecordSerializationSchema.builder() \
        .set_topic(output_topic) \
        .set_key_serialization_schema(PassthroughSerializationSchema(j_serialization_schema=j_json_key_serilization_schema )) \
        .set_value_serialization_schema(PassthroughSerializationSchema(j_serialization_schema=j_json_value_serialization_schema)) \
        .build()

    kafka_sink = KafkaSink.builder() \
        .set_bootstrap_servers(bootstrap_servers) \
        .set_record_serializer(key_value_kafka_serialization_schema) \
        .set_delivery_guarantee(DeliveryGuarantee.NONE) \
        .set_property('security.protocol', 'SASL_SSL') \
        .set_property('sasl.mechanism', 'PLAIN') \
        .set_property('sasl.jaas.config',
                      f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{kafka_user}" password="{kafka_password}";') \
        .set_property('ssl.ca.location', 'ISRG Root X1.crt') \
        .build()

    conversations_ds = env.from_source(source=conversations_kafka_source,
                                       watermark_strategy=WatermarkStrategy.no_watermarks(),
                                       source_name="KafkaSource")

    # ignore close for now
    # conversations: open
    conversations_ds \
        .filter(lambda message: json.loads(message['key'].decode('utf-8'))['type'] == 'open') \
        .key_by(lambda message: json.loads(message['key'].decode('utf-8'))['conversationId'], Types.STRING()) \
        .map(lambda message: initial_greeting(
            json.loads(message['key'].decode('utf-8'))['callerId'],
            json.loads(message['key'].decode('utf-8'))['conversationId'],
            json.loads(message['key'].decode('utf-8')).get('conversation_module', conversation_module_default),
            message['value'].decode('utf-8')),
            Types.STRING()) \
        .sink_to(kafka_sink)
        

    #conversations: transcription
    conversations_ds \
        .filter(lambda message: json.loads(message['key'].decode('utf-8'))['channel'] == 'MONKEY_JACKET') \
        .filter(lambda message: json.loads(message['key'].decode('utf-8'))['type'] == 'transcription') \
        .filter(lambda message: message['value'].decode('utf-8') and len(message['value'].decode('utf-8')) > 0) \
        .key_by(lambda message: json.loads(message['key'].decode('utf-8'))['conversationId'], Types.STRING()) \
        .map(lambda message: next_response(
            json.loads(message['key'].decode('utf-8'))['callerId'],
            json.loads(message['key'].decode('utf-8'))['conversationId'],
            json.loads(message['key'].decode('utf-8')).get('conversation_module', conversation_module_default),
            message['value'].decode('utf-8')),
            Types.STRING()) \
        .sink_to(kafka_sink)

    print(f'{current_ts()}: starting Flink job')
    env.execute("genesys-chat")

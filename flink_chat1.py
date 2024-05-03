import json
import os
import time

from pyflink.common import WatermarkStrategy
from pyflink.common.serialization import DeserializationSchema, SerializationSchema
from pyflink.common.typeinfo import Types
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import DeliveryGuarantee
from pyflink.datastream.connectors.kafka import KafkaSource, \
    KafkaSink, KafkaRecordSerializationSchema, KafkaOffsetsInitializer
from pyflink.java_gateway import get_gateway

import conversation_manager


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


class JsonSerializationSchema(SerializationSchema):
    def serialize(self, value):
        return json.dumps(value)


class BytesSerializationSchema(SerializationSchema):
    def serialize(self, value):
        print('serializer:', value)
        return str(value)


class KeyValueSerializationSchema(SerializationSchema):
    def serialize(self, value):
        # Assuming `value` is a tuple (key, value)
        key, val = value
        # Serialize key and value as bytes, separated by a comma (for example)
        return (key.encode('utf-8'), val.encode('utf-8'))


def initial_greeting(caller_id, conversation_id):
    t1 = time.time()
    print(0.0, 'received call, generating initial greeting')
    # {"text": greeting_text, "audio": bytes}
    greeting = conversation_manager.get_initial_greeting(caller_id, conversation_id)
    print(f"{time.time() - t1}s initial greeting and audio generated: {greeting['text']}, {len(greeting['audio']) if greeting['audio'] else 0} bytes")
    key = json.dumps({'conversationId': conversation_id}).encode('utf-8')
    # print(f"${time.time() - t1}s initial greeting generated: {greeting['text']}, {len(greeting['audio'])} bytes")
    return key, greeting['audio']


def next_response(caller_id, conversation_id, request_phrase):
    t1 = time.time()
    print(f"0.0s received phrase, generating response: {request_phrase}")
    response = conversation_manager.get_response(caller_id, conversation_id, request_phrase)
    print(f'{time.time() - t1}s response generated: {response["text"]}, {len(response["audio"])} bytes')
    key = json.dumps({'conversationId': conversation_id}).encode('utf-8')
    return key, response['audio']


if __name__ == "__main__":
    # Kafka configuration
    conversations_topic = "haystack-voice-vishing-ai-conversations"
    output_topic = "haystack-voice-vishing-ai-output"
    analysis_topic = "haystack-voice-vishing-ai-analysis"
    bootstrap_servers = "pkc-56d1g.eastus.azure.confluent.cloud:9092"
    group_id = "vishing-chat-group"

    env = StreamExecutionEnvironment.get_execution_environment()
    print('Flink parallelism:', env.get_parallelism())

    home_dir = os.path.expanduser('~')
    # env.add_jars(f"file://{home_dir}/.m2/repository/org/apache/flink/flink-connector-kafka/3.1.0-1.18/flink-connector-kafka-3.1.0-1.18.jar")
    # env.add_jars(f"file://{home_dir}/.m2/repository/org/apache/kafka/kafka-clients/3.3.1/kafka-clients-3.3.1.jar")
    working_dir = os.getcwd()
    # env.add_jars(f"file://{home_path}/GoodLabs/GMM_voiceID/java/target/gmm-flink-java-1.0-SNAPSHOT.jar")
    jar_path = f"file://{working_dir}/java/target/gmm-flink-java-1.0-SNAPSHOT.jar"
    env.add_jars(jar_path)
    print(f'added jar {jar_path}')

    gate_way = get_gateway()
    j_char_set = gate_way.jvm.java.nio.charset.Charset.forName('UTF-8')
    j_simple_string_serialization_schema = gate_way \
        .jvm.org.apache.flink.api.common.serialization.SimpleStringSchema(j_char_set)
    j_byte_array_deserialization_schema = gate_way \
        .jvm.studio.goodlabs.vishing.KafkaMapByteArrayDeserializationSchema()
    j_byte_array_serialization_schema = gate_way \
        .jvm.studio.goodlabs.vishing.KafkaValueSerializationSchema()
    j_json_serialization_schema = gate_way \
        .jvm.org.apache.flink.formats.json.JsonSerializationSchema()

    kafka_user = os.environ["KAFKA_GENESYS_CHAT_USER"]
    kafka_password = os.environ["KAFKA_GENESYS_CHAT_PASSWORD"]

    conversations_kafka_source = KafkaSource.builder() \
        .set_bootstrap_servers(bootstrap_servers) \
        .set_topics(conversations_topic) \
        .set_group_id(group_id) \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_deserializer(BinaryDeserializationSchema(j_deserialization_schema=j_byte_array_deserialization_schema)) \
        .set_property('security.protocol', 'SASL_SSL') \
        .set_property('sasl.mechanism', 'PLAIN') \
        .set_property('sasl.jaas.config', f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{kafka_user}" password="{kafka_password}";') \
        .set_property('ssl.ca.location', 'ISRG Root X1.crt') \
        .build()

    inference_kafka_source = KafkaSource.builder() \
        .set_bootstrap_servers(bootstrap_servers) \
        .set_topics(analysis_topic) \
        .set_group_id(group_id) \
        .set_starting_offsets(KafkaOffsetsInitializer.latest()) \
        .set_deserializer(BinaryDeserializationSchema(j_deserialization_schema=j_byte_array_deserialization_schema)) \
        .set_property('security.protocol', 'SASL_SSL') \
        .set_property('sasl.mechanism', 'PLAIN') \
        .set_property('sasl.jaas.config', f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{kafka_user}" password="{kafka_password}";') \
        .set_property('ssl.ca.location', 'ISRG Root X1.crt') \
        .build()

    key_value_kafka_serialization_schema = KafkaRecordSerializationSchema.builder() \
        .set_topic(output_topic) \
        .set_key_serialization_schema(BytesSerializationSchema(j_serialization_schema=j_byte_array_serialization_schema)) \
        .set_value_serialization_schema(BytesSerializationSchema(j_serialization_schema=j_byte_array_serialization_schema)) \
        .build()

    kafka_sink = KafkaSink.builder() \
        .set_bootstrap_servers(bootstrap_servers) \
        .set_record_serializer(key_value_kafka_serialization_schema) \
        .set_delivery_guarantee(DeliveryGuarantee.NONE) \
        .set_property('security.protocol', 'SASL_SSL') \
        .set_property('sasl.mechanism', 'PLAIN') \
        .set_property('sasl.jaas.config', f'org.apache.kafka.common.security.plain.PlainLoginModule required username="{kafka_user}" password="{kafka_password}";') \
        .set_property('ssl.ca.location', 'ISRG Root X1.crt') \
        .build()

    ds = env.from_source(source=conversations_kafka_source,
                         watermark_strategy=WatermarkStrategy.no_watermarks(),
                         source_name="KafkaSource")

    # ignore close for now
    # conversations: open
    ds \
        .filter(lambda message: json.loads(message['key'].decode('utf-8'))['type'] == 'open') \
        .key_by(lambda message: json.loads(message['key'].decode('utf-8'))['conversationId'], Types.STRING()) \
        .map(lambda message: initial_greeting('caller1', json.loads(message['key'].decode('utf-8'))['conversationId'])) \
        .sink_to(kafka_sink)

    # conversations: transcription
    ds \
        .filter(lambda message: json.loads(message['key'].decode('utf-8'))['channel'] == 'EXTERNAL') \
        .filter(lambda message: json.loads(message['key'].decode('utf-8'))['type'] == 'transcription') \
        .filter(lambda message: message['value'].decode('utf-8') and len(message['value'].decode('utf-8')) > 0) \
        .key_by(lambda message: json.loads(message['key'].decode('utf-8'))['conversationId'], Types.STRING()) \
        .map(lambda message: next_response(
            'caller1', json.loads(message['key'].decode('utf-8'))['conversationId'], message['value'].decode('utf-8'))) \
        .sink_to(kafka_sink)

    # inference
    # TODO

    print('starting Flink job')
    env.execute("genesys-chat")

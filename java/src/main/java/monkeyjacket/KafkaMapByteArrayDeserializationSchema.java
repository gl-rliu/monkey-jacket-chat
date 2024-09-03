package studio.goodlabs.monkeyjacket;

import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.api.common.typeinfo.Types;
import org.apache.flink.connector.kafka.source.reader.deserializer.KafkaRecordDeserializationSchema;
import org.apache.flink.util.Collector;
import org.apache.kafka.clients.consumer.ConsumerRecord;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

public class KafkaMapByteArrayDeserializationSchema implements KafkaRecordDeserializationSchema<Map<String, byte[]>> {

    @Override
    public void deserialize(ConsumerRecord<byte[], byte[]> record, Collector<Map<String, byte[]>> out) throws IOException {
        Map<String, byte[]> map = new HashMap<>(2);
        map.put("key", record.key());
        map.put("value", record.value());
        out.collect(map);
    }

    @Override
    public TypeInformation<Map<String, byte[]>> getProducedType() {
        return Types.MAP(Types.STRING, (TypeInformation<byte[]>) Types.PRIMITIVE_ARRAY(Types.BYTE));
    }

}

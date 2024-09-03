package studio.goodlabs.monkeyjacket;

import org.apache.flink.api.common.serialization.SerializationSchema;
import org.json.JSONObject;

public class KafkaKeyJsonSerializationSchema implements SerializationSchema<String> {

    @Override
    public byte[] serialize(String element) {

        JSONObject jsonObject = new JSONObject(element);
        String key = jsonObject.get("key").toString();
        return key.getBytes();
    }
}
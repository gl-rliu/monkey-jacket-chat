package studio.goodlabs.monkeyjacket;

import org.apache.flink.api.common.serialization.SerializationSchema;
import org.json.JSONObject;

public class KafkaValueJsonSerializationSchema implements SerializationSchema<String>  {

    @Override
    public byte[] serialize(String element) {

        JSONObject jsonObject = new JSONObject(element);
        String key = jsonObject.get("value").toString();
        return key.getBytes();
    }

    public static void main(String[] args) {
        String input = "{\"key\": \"{\\\"conversationId\\\": \\\"test_key_A\\\"}\", \"value\": [\"Hey, emmm, hi.\"]}";

        JSONObject jsonObject = new JSONObject(input);
        System.out.println(jsonObject.get("key").toString());
        System.out.println(jsonObject.get("value").toString());
    }
}

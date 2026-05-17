import java.io.IOException;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;

/**
 * MOSS-TTS-Nano API Java 调用示例
 * 
 * 依赖: Java 11+ (使用 HttpClient)
 */
public class MossTtsClient {
    
    private static final String API_BASE_URL = "http://localhost:8005";
    private static final HttpClient httpClient = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(30))
        .build();
    
    /**
     * 调用 MOSS-TTS-Nano API 生成 MP3 音频
     * 
     * @param text 要转换的文本
     * @param voice 发音人ID，如 "zh_1"
     * @return MP3 音频数据，失败返回 null
     */
    public static byte[] synthesizeToMp3(String text, String voice) {
        try {
            // URL 编码文本和语音参数
            String encodedText = URLEncoder.encode(text, StandardCharsets.UTF_8);
            String encodedVoice = URLEncoder.encode(voice, StandardCharsets.UTF_8);
            
            // 构建请求 URL（参数在查询字符串中）
            String url = API_BASE_URL + "/tts?text=" + encodedText + "&voice=" + encodedVoice;
            
            System.out.println("Calling MOSS-TTS-Nano API: " + url);
            
            // 构建 HTTP POST 请求（Body 为空）
            HttpRequest request = HttpRequest.newBuilder()
                .uri(java.net.URI.create(url))
                .timeout(Duration.ofSeconds(60))
                .POST(HttpRequest.BodyPublishers.noBody())
                .header("Accept", "audio/mpeg")
                .build();
            
            // 发送请求并获取响应
            HttpResponse<byte[]> response = httpClient.send(
                request, 
                HttpResponse.BodyHandlers.ofByteArray()
            );
            
            if (response.statusCode() != 200) {
                System.err.println("API error: status=" + response.statusCode());
                System.err.println("Response: " + new String(response.body(), StandardCharsets.UTF_8));
                return null;
            }
            
            byte[] audioData = response.body();
            System.out.println("Received " + audioData.length + " bytes of MP3 audio");
            
            // 打印响应头信息
            String synthesisTime = response.headers().firstValue("X-Synthesis-Time").orElse("N/A");
            String audioLength = response.headers().firstValue("X-Audio-Length").orElse("N/A");
            System.out.println("Synthesis time: " + synthesisTime + "s");
            System.out.println("Audio length: " + audioLength + " bytes");
            
            return audioData;
            
        } catch (Exception e) {
            System.err.println("API call failed: " + e.getMessage());
            e.printStackTrace();
            return null;
        }
    }
    
    /**
     * 保存音频数据到文件
     * 
     * @param audioData MP3 音频数据
     * @param outputPath 输出文件路径
     * @return 是否保存成功
     */
    public static boolean saveToFile(byte[] audioData, String outputPath) {
        try {
            Path path = Path.of(outputPath);
            Files.write(path, audioData);
            System.out.println("Audio saved to: " + outputPath);
            System.out.println("File size: " + audioData.length + " bytes");
            return true;
        } catch (IOException e) {
            System.err.println("Failed to save file: " + e.getMessage());
            return false;
        }
    }
    
    public static void main(String[] args) {
        System.out.println("========================================");
        System.out.println("MOSS-TTS-Nano API Java Client Example");
        System.out.println("========================================\n");
        
        // 测试 1: 中文合成
        System.out.println("Test 1: Chinese synthesis");
        byte[] chineseAudio = synthesizeToMp3(
            "欢迎使用 MOSS-TTS-Nano API 服务。", 
            "zh_1"
        );
        if (chineseAudio != null) {
            saveToFile(chineseAudio, "output_chinese.mp3");
        }
        System.out.println();
        
        // 测试 2: 英文合成
        System.out.println("Test 2: English synthesis");
        byte[] englishAudio = synthesizeToMp3(
            "Hello, this is a test of the MOSS-TTS-Nano API.", 
            "zh_1"
        );
        if (englishAudio != null) {
            saveToFile(englishAudio, "output_english.mp3");
        }
        System.out.println();
        
        // 测试 3: 长文本合成
        System.out.println("Test 3: Long text synthesis");
        byte[] longAudio = synthesizeToMp3(
            "这是一个较长的测试文本，用于验证 API 服务在处理长文本时的表现。" +
            "MOSS-TTS-Nano 是一个轻量级的语音合成模型，支持多种语言和声音克隆功能。", 
            "zh_1"
        );
        if (longAudio != null) {
            saveToFile(longAudio, "output_long.mp3");
        }
        
        System.out.println("\n========================================");
        System.out.println("All tests completed!");
        System.out.println("========================================");
    }
}

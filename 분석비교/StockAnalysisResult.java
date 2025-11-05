public class StockAnalysisResult {
    private String status;
    private String code;
    private String name;
    private String analysis_date;
    private String pattern_type;
    private boolean pattern_detected;
    private DetectionInfo detection_info; // 내부 클래스 또는 객체로 정의
    private String chart_image_base64;
    private String error; // 오류 발생 시 사용

    // Getter와 Setter (Jackson이 사용)
    // ...
}

public class DetectionInfo {
    private double entry_price;
    private double neckline_price;
    private String first_trough_date;
    private String second_trough_date;
    private double confidence_score;
    // Getter와 Setter
    // ...
}
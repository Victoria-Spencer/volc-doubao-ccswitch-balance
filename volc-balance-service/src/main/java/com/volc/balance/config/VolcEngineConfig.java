package com.volc.balance.config;

import com.volcengine.ApiClient;
import com.volcengine.billing.BillingApi;
import com.volcengine.sign.Credentials;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class VolcEngineConfig {

    @Value("${volcengine.access-key}")
    private String accessKey;

    @Value("${volcengine.secret-key}")
    private String secretKey;

    @Value("${volcengine.region:cn-beijing}")
    private String region;

    /**
     * 按官方示例注入BillingApi，使用ApiClient+Credentials方式
     */
    @Bean
    public BillingApi billingApi() {
        // 初始化ApiClient
        ApiClient apiClient = new ApiClient()
                .setCredentials(Credentials.getCredentials(accessKey, secretKey)) // 鉴权
                .setRegion(region); // 设置地域

        // 创建BillingApi实例
        return new BillingApi(apiClient);
    }
}
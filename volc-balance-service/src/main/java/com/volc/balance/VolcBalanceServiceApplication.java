package com.volc.balance;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;

@SpringBootApplication
public class VolcBalanceServiceApplication {

    public static ConfigurableApplicationContext context;

    public static void main(String[] args) {
        context = SpringApplication.run(VolcBalanceServiceApplication.class, args);
    }

    /**
     * 对外提供关闭服务方法（供CC-Switch调用）
     */
    public static void shutdown() {
        if (context != null) {
            context.close();
            System.exit(0);
        }
    }
}

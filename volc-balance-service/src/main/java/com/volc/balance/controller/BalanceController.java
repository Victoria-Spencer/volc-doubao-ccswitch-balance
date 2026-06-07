package com.volc.balance.controller;

import com.volc.balance.service.BalanceQueryService;
import com.volc.balance.vo.BalanceVO;
import com.volc.balance.VolcBalanceServiceApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class BalanceController {

    private final BalanceQueryService balanceQueryService;

    // 构造函数注入服务
    public BalanceController(BalanceQueryService balanceQueryService) {
        this.balanceQueryService = balanceQueryService;
    }

    /**
     * 核心接口：查询火山引擎账户余额
     */
    @GetMapping("/api/volc/balance")
    public BalanceVO getBalance() {
        return balanceQueryService.queryBalance();
    }

    /**
     * 关闭接口：CC-Switch 查询完成后调用，自动停止服务
     */
    @GetMapping("/shutdown")
    public String shutdown() {
        // 异步关闭，避免请求阻塞
        new Thread(VolcBalanceServiceApplication::shutdown).start();
        return "Service Shutting Down";
    }
}
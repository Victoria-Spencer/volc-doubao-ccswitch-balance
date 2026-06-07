package com.volc.balance.service;

import com.volc.balance.vo.BalanceVO;
import com.volcengine.ApiException;
import com.volcengine.billing.BillingApi;
import com.volcengine.billing.model.QueryBalanceAcctRequest;
import com.volcengine.billing.model.QueryBalanceAcctResponse;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;

@Service
public class BalanceQueryService {

    private final BillingApi billingApi;

    public BalanceQueryService(BillingApi billingApi) {
        this.billingApi = billingApi;
    }

    public BalanceVO queryBalance() {
        try {
            QueryBalanceAcctRequest request = new QueryBalanceAcctRequest();
            // 调用官方API
            QueryBalanceAcctResponse response = billingApi.queryBalanceAcct(request);

            BigDecimal remainingBalance = new BigDecimal(response.getAvailableBalance());

            // 构造符合 CC-Switch 规范的返回对象
            BalanceVO balanceVO = new BalanceVO();
            balanceVO.setIsValid(true);
            balanceVO.setInvalidMessage(null);
            balanceVO.setRemaining(remainingBalance);
            balanceVO.setUnit("CNY");
            balanceVO.setPlanName("火山引擎账户余额");
            balanceVO.setTotal(null);       // 火山接口无总额度，置空
            balanceVO.setUsed(null);        // 火山接口无已用额度，置空
            balanceVO.setExtra("现金余额：" + response.getCashBalance());

            return balanceVO;
        } catch (ApiException e) {
            // 按平台格式返回错误信息，不抛异常
            BalanceVO errorVO = new BalanceVO();
            errorVO.setIsValid(false);
            errorVO.setInvalidMessage("余额查询失败：" + e.getResponseBody());
            errorVO.setRemaining(null);
            errorVO.setUnit(null);
            errorVO.setPlanName(null);
            errorVO.setTotal(null);
            errorVO.setUsed(null);
            errorVO.setExtra(null);
            return errorVO;
        }
    }
}
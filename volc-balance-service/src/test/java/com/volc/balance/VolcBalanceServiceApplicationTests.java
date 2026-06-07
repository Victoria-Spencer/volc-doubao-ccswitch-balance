package com.volc.balance;

import com.volc.balance.service.BalanceQueryService;
import com.volc.balance.vo.BalanceVO;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class VolcBalanceServiceApplicationTests {

    @Autowired
    private BalanceQueryService balanceQueryService;

    @Test
    void testQueryBalance() {
        // 直接调用服务查询余额
        BalanceVO balanceVO = balanceQueryService.queryBalance();

        // 控制台打印结果，方便查看
        System.out.println("=== 余额查询结果 ===");
        System.out.println("是否有效：" + balanceVO.getIsValid());
        System.out.println("剩余额度：" + balanceVO.getRemaining());
        System.out.println("单位：" + balanceVO.getUnit());
        System.out.println("扩展信息：" + balanceVO.getExtra());
    }
}

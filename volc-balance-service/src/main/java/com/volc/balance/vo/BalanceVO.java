package com.volc.balance.vo;

import java.math.BigDecimal;

/**
 * 余额查询返回实体（适配 CC-Switch Extractor 格式）
 */
public class BalanceVO {
    // 套餐是否有效
    private Boolean isValid;
    // 失效原因
    private String invalidMessage;
    // 剩余额度 = (现金余额 - 冻结金额) + 信控额度 - 欠费金额
    private BigDecimal remaining;
    // 单位
    private String unit;
    // 套餐名称
    private String planName;
    // 总额度
    private BigDecimal total;
    // 已用额度
    private BigDecimal used;
    // 扩展字段
    private String extra;

    public BalanceVO() {
    }

    public BalanceVO(Boolean isValid, String invalidMessage, BigDecimal remaining, String unit, String planName, BigDecimal total, BigDecimal used, String extra) {
        this.isValid = isValid;
        this.invalidMessage = invalidMessage;
        this.remaining = remaining;
        this.unit = unit;
        this.planName = planName;
        this.total = total;
        this.used = used;
        this.extra = extra;
    }

    // ============ Setter ============
    public void setRemaining(BigDecimal remaining) {
        this.remaining = remaining;
    }

    public void setUnit(String unit) {
        this.unit = unit;
    }

    public void setIsValid(Boolean isValid) {
        this.isValid = isValid;
    }

    public void setInvalidMessage(String invalidMessage) {
        this.invalidMessage = invalidMessage;
    }

    public void setPlanName(String planName) {
        this.planName = planName;
    }

    public void setTotal(BigDecimal total) {
        this.total = total;
    }

    public void setUsed(BigDecimal used) {
        this.used = used;
    }

    public void setExtra(String extra) {
        this.extra = extra;
    }

    // ============ Getter ============
    public Boolean getIsValid() {
        return isValid;
    }

    public String getInvalidMessage() {
        return invalidMessage;
    }

    public BigDecimal getRemaining() {
        return remaining;
    }

    public String getUnit() {
        return unit;
    }

    public String getPlanName() {
        return planName;
    }

    public BigDecimal getTotal() {
        return total;
    }

    public BigDecimal getUsed() {
        return used;
    }

    public String getExtra() {
        return extra;
    }
}
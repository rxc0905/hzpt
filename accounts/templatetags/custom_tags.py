from django import template
import json

register = template.Library()


@register.filter
def to_json(value):
    """将Python对象转为JSON字符串"""
    return json.dumps(value, ensure_ascii=False)


@register.filter
def credit_class(score):
    """根据信誉分返回CSS类"""
    if score >= 80:
        return 'credit-high'
    elif score >= 60:
        return 'credit-medium'
    return 'credit-low'


@register.filter
def star_range(score):
    """生成星星列表"""
    return range(1, 6)

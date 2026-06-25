"""
sample_code.py — AI Coding 教学 Demo 用示例文件

这个文件故意混合了"好代码"和"坏代码"的写法，
方便在课堂上展示 MCP 工具的分析能力。
"""

import os
import sys
from datetime import datetime
from typing import List, Optional, Dict, Any


# =========================================================================
# 简单的工具函数
# =========================================================================

def greet(name: str) -> str:
    """向用户问好"""
    return f"你好，{name}！"


def calculate_sum(numbers: List[float]) -> float:
    """
    计算数字列表的总和。

    参数
    ----
    numbers : List[float]
        要相加的数字列表

    返回
    ----
    float : 总和
    """
    total = 0.0
    for num in numbers:
        total += num
    return total


# =========================================================================
# 一个故意写得复杂的函数（展示复杂度分析）
# =========================================================================

def process_order(order: Dict[str, Any], user: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> str:
    """
    处理订单 — 故意写了多个分支来展示圈复杂度分析。

    这个函数包含了 if/elif/else/for/while 等多种控制流，
    圈复杂度较高，适合在课堂上作为反面例子。
    """
    if not order:
        return "订单为空"

    if not user:
        return "用户不存在"

    if config is None:
        config = {}

    # 检查订单状态
    status = order.get("status", "pending")
    if status == "pending":
        if order.get("amount", 0) <= 0:
            return "订单金额无效"
        elif order.get("amount", 0) > 100000:
            return "订单金额过大，需要人工审核"
        else:
            # 正常处理
            pass
    elif status == "cancelled":
        return "订单已取消"
    elif status == "refunded":
        return "订单已退款"
    elif status == "shipped" or status == "delivered":
        return "订单已发货或已送达，无法修改"
    else:
        return f"未知订单状态：{status}"

    # 检查用户权限
    user_role = user.get("role", "guest")
    if user_role == "admin":
        # 管理员可以处理任何订单
        pass
    elif user_role == "vip":
        if order.get("amount", 0) > 50000:
            return "VIP 用户的大额订单需要二次确认"
    elif user_role == "guest":
        return "访客不能处理订单"
    else:
        if config.get("strict_mode", False):
            return f"未知用户角色：{user_role}，且开启了严格模式"

    # 计算折扣
    discount = 0.0
    amount = order.get("amount", 0)
    if amount > 1000 and amount <= 5000:
        discount = 0.05
    elif amount > 5000 and amount <= 20000:
        discount = 0.1
    elif amount > 20000 and amount <= 50000:
        discount = 0.15
    elif amount > 50000:
        discount = 0.2

    # 应用优惠券（如果有）
    coupon = order.get("coupon")
    if coupon:
        coupon_type = coupon.get("type", "fixed")
        coupon_value = coupon.get("value", 0)
        if coupon_type == "fixed":
            discount = max(discount, coupon_value / amount)
        elif coupon_type == "percentage":
            discount = max(discount, coupon_value / 100)
        else:
            print(f"未知优惠券类型：{coupon_type}")

    final_amount = amount * (1 - discount)

    # 记录日志
    log_items = []
    log_items.append(f"订单 {order.get('id', 'unknown')} 已处理")
    log_items.append(f"原始金额：{amount}")
    log_items.append(f"折扣：{discount * 100:.1f}%")
    log_items.append(f"最终金额：{final_amount:.2f}")
    log_items.append(f"处理时间：{datetime.now()}")

    for item in log_items:
        print(item)

    return f"订单处理完成，最终金额：{final_amount:.2f} 元"


# =========================================================================
# 类定义
# =========================================================================

class UserManager:
    """
    用户管理器 — 负责用户的创建、查询和权限管理。
    这个类展示了 MCP 工具对类结构的分析能力。
    """

    def __init__(self):
        self._users: Dict[str, Dict[str, Any]] = {}

    def add_user(self, user_id: str, name: str, role: str = "user") -> bool:
        if user_id in self._users:
            return False
        self._users[user_id] = {
            "id": user_id,
            "name": name,
            "role": role,
            "created_at": datetime.now().isoformat()
        }
        return True

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._users.get(user_id)

    def list_users(self) -> List[Dict[str, Any]]:
        return list(self._users.values())

    def delete_user(self, user_id: str) -> bool:
        if user_id not in self._users:
            return False
        del self._users[user_id]
        return True


class DataProcessor:
    """
    数据处理器 — 演示继承和多态的代码结构。
    """

    def __init__(self, name: str):
        self.name = name
        self._data: List[Any] = []

    def load(self, data: List[Any]) -> None:
        self._data = data

    def process(self) -> List[Any]:
        """子类应该重写此方法"""
        raise NotImplementedError

    def save(self, output_path: str) -> bool:
        try:
            with open(output_path, "w") as f:
                f.write(str(self._data))
            return True
        except IOError:
            return False


class CSVProcessor(DataProcessor):
    """CSV 数据处理器 — 继承自 DataProcessor"""

    def process(self) -> List[List[str]]:
        result = []
        for row in self._data:
            if isinstance(row, str):
                result.append(row.split(","))
            else:
                result.append([str(row)])
        return result


if __name__ == "__main__":
    # 简单测试
    mgr = UserManager()
    mgr.add_user("001", "张三", "vip")
    mgr.add_user("002", "李四", "admin")
    print(mgr.list_users())

    proc = CSVProcessor("测试处理器")
    proc.load(["a,b,c", "1,2,3", "x,y,z"])
    print(proc.process())

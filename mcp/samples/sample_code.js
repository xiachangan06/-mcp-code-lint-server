/**
 * sample_code.js — AI Coding 教学 Demo 用示例文件（JavaScript 版本）
 *
 * 这个文件与 sample_code.py 功能相似但用不同风格编写，
 * 方便在课堂上展示 MCP 工具的跨语言分析和对比能力。
 */

const fs = require("fs");
const path = require("path");

// =========================================================================
// 基础工具函数
// =========================================================================

/**
 * 向用户问好
 */
function greet(name) {
  return `Hello, ${name}!`;
}

/**
 * 计算数字数组的总和
 */
function calculateSum(numbers) {
  return numbers.reduce((total, num) => total + num, 0);
}

/**
 * 找出数组中的最大值和最小值
 */
function findMinMax(numbers) {
  if (!numbers || numbers.length === 0) {
    return { min: null, max: null };
  }

  let min = Infinity;
  let max = -Infinity;

  for (const num of numbers) {
    if (num < min) min = num;
    if (num > max) max = num;
  }

  return { min, max };
}

// =========================================================================
// 复杂业务逻辑（展示复杂度分析）
// =========================================================================

/**
 * 处理用户订单 — 多个分支，高圈复杂度
 */
function processOrder(order, user, config = {}) {
  // 参数校验
  if (!order) return { success: false, message: "订单为空" };
  if (!user) return { success: false, message: "用户不存在" };

  const { status = "pending", amount = 0, coupon = null } = order;
  const { role = "guest" } = user;
  let discount = 0;

  // 检查订单状态
  if (status === "pending") {
    if (amount <= 0) {
      return { success: false, message: "订单金额无效" };
    } else if (amount > 100000) {
      return { success: false, message: "金额过大，需人工审核" };
    }
  } else if (status === "cancelled") {
    return { success: false, message: "订单已取消" };
  } else if (status === "refunded") {
    return { success: false, message: "订单已退款" };
  } else if (status === "shipped" || status === "delivered") {
    return { success: false, message: "订单已发货或已送达" };
  } else {
    return { success: false, message: `未知状态：${status}` };
  }

  // 权限检查
  if (role === "guest") {
    return { success: false, message: "访客不能处理订单" };
  }

  // 计算折扣
  if (amount > 1000 && amount <= 5000) discount = 0.05;
  else if (amount > 5000 && amount <= 20000) discount = 0.1;
  else if (amount > 20000 && amount <= 50000) discount = 0.15;
  else if (amount > 50000) discount = 0.2;

  // 优惠券
  if (coupon) {
    const couponDiscount =
      coupon.type === "fixed"
        ? coupon.value / amount
        : coupon.type === "percentage"
          ? coupon.value / 100
          : 0;
    discount = Math.max(discount, couponDiscount);
  }

  const finalAmount = amount * (1 - discount);

  // 日志
  console.log(`订单 ${order.id || "unknown"} 已处理`);
  console.log(`原始金额：${amount}，折扣：${(discount * 100).toFixed(1)}%`);
  console.log(`最终金额：${finalAmount.toFixed(2)}`);

  return {
    success: true,
    message: "订单处理完成",
    originalAmount: amount,
    discount: discount,
    finalAmount: finalAmount,
  };
}

// =========================================================================
// 类定义（ES6 Class）
// =========================================================================

/**
 * 用户管理器
 */
class UserManager {
  constructor() {
    this._users = new Map();
  }

  addUser(userId, name, role = "user") {
    if (this._users.has(userId)) return false;
    this._users.set(userId, {
      id: userId,
      name,
      role,
      createdAt: new Date().toISOString(),
    });
    return true;
  }

  getUser(userId) {
    return this._users.get(userId) || null;
  }

  listUsers() {
    return Array.from(this._users.values());
  }

  deleteUser(userId) {
    return this._users.delete(userId);
  }
}

/**
 * 数据处理器基类
 */
class DataProcessor {
  constructor(name) {
    this.name = name;
    this._data = [];
  }

  load(data) {
    this._data = data;
  }

  process() {
    throw new Error("子类必须实现 process 方法");
  }

  save(outputPath) {
    try {
      fs.writeFileSync(outputPath, JSON.stringify(this._data));
      return true;
    } catch (err) {
      console.error(`保存失败：${err.message}`);
      return false;
    }
  }
}

/**
 * CSV 数据处理器
 */
class CSVProcessor extends DataProcessor {
  process() {
    return this._data.map((row) => {
      if (typeof row === "string") {
        return row.split(",");
      }
      return [String(row)];
    });
  }
}

// =========================================================================
// 模块导出
// =========================================================================

module.exports = {
  greet,
  calculateSum,
  findMinMax,
  processOrder,
  UserManager,
  DataProcessor,
  CSVProcessor,
};

// =========================================================================
// 自测
// =========================================================================

if (require.main === module) {
  const mgr = new UserManager();
  mgr.addUser("001", "Alice", "vip");
  mgr.addUser("002", "Bob", "admin");
  console.log(mgr.listUsers());

  const order = {
    id: "ORD-001",
    amount: 15000,
    status: "pending",
    coupon: { type: "fixed", value: 500 },
  };
  const user = { role: "vip" };
  console.log(processOrder(order, user));
}

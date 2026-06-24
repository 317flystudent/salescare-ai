CREATE DATABASE IF NOT EXISTS salescare_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE salescare_ai;

CREATE TABLE IF NOT EXISTS knowledge_base (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  category VARCHAR(100) NOT NULL,
  title VARCHAR(255) NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  keywords VARCHAR(500) NOT NULL DEFAULT '',
  updated_at VARCHAR(40) NOT NULL,
  UNIQUE KEY uq_knowledge_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sessions (
  id VARCHAR(64) PRIMARY KEY,
  channel VARCHAR(40) NOT NULL DEFAULT 'web',
  created_at VARCHAR(40) NOT NULL,
  updated_at VARCHAR(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS messages (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  session_id VARCHAR(64) NOT NULL,
  role VARCHAR(20) NOT NULL,
  content LONGTEXT NOT NULL,
  intent VARCHAR(100),
  metadata_json LONGTEXT NOT NULL,
  created_at VARCHAR(40) NOT NULL,
  INDEX idx_messages_session (session_id, created_at),
  CONSTRAINT fk_messages_session
    FOREIGN KEY (session_id) REFERENCES sessions(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS demo_orders (
  order_no VARCHAR(32) PRIMARY KEY,
  customer_name VARCHAR(80) NOT NULL,
  product_name VARCHAR(120) NOT NULL,
  status VARCHAR(80) NOT NULL,
  logistics_status VARCHAR(255) NOT NULL,
  payment_status VARCHAR(40) NOT NULL,
  aftersale_status VARCHAR(120) NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  city VARCHAR(80) NOT NULL,
  created_at VARCHAR(40) NOT NULL,
  updated_at VARCHAR(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS handoff_tickets (
  ticket_no VARCHAR(32) PRIMARY KEY,
  session_id VARCHAR(64),
  customer_name VARCHAR(80) NOT NULL,
  reason TEXT NOT NULL,
  priority VARCHAR(20) NOT NULL,
  status VARCHAR(40) NOT NULL,
  assigned_team VARCHAR(80) NOT NULL,
  expected_response VARCHAR(120) NOT NULL,
  created_at VARCHAR(40) NOT NULL,
  updated_at VARCHAR(40) NOT NULL,
  INDEX idx_handoff_tickets_session (session_id, updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO knowledge_base
  (category, title, question, answer, keywords, updated_at)
VALUES
  ('产品咨询', '悦行 S1 城市通勤版', '悦行 S1 适合什么人群？续航和核心配置是什么？', '悦行 S1 面向城市通勤用户，标称续航 65 公里，支持 NFC 解锁、前后双碟刹、智能防盗和手机 App 车况查看。适合每天 5 到 20 公里的上下班、校园和门店配送场景。', 'S1,通勤,续航,配置,NFC,防盗,电动车', '2026-06-09T00:00:00+00:00'),
  ('产品咨询', '悦行 Pro 家庭长续航版', '悦行 Pro 和 S1 有什么区别？', '悦行 Pro 主打长续航和舒适性，标称续航 95 公里，配备更大容量锂电池、加宽坐垫和后座脚踏。S1 更轻便，适合短途通勤；Pro 更适合家庭共享、较长距离通勤或外卖配送。', 'Pro,S1,区别,长续航,家庭,配送', '2026-06-09T00:00:00+00:00'),
  ('价格与促销', '购车优惠政策', '现在购买悦行电动车有什么优惠？', '当前标准优惠包括旧车置换最高抵扣 500 元、学生认证减免 200 元、门店自提赠送头盔和首年基础保养。具体优惠会随城市和门店库存变化，建议提供所在城市后由客服确认。', '价格,优惠,促销,置换,学生,头盔,保养', '2026-06-09T00:00:00+00:00'),
  ('订单查询', '订单状态查询', '如何查询订单发货、物流和门店自提状态？', '用户可提供订单号或下单手机号后四位。线上订单通常在付款后 24 小时内出库，物流单号会通过短信和 App 推送。门店自提订单到店后会发送提车码，需携带身份证或下单手机号核验。', '订单,物流,发货,自提,提车码,手机号', '2026-06-09T00:00:00+00:00'),
  ('退换货', '七天无理由退换', '悦行电动车支持七天无理由退换吗？', '线上购买且未上牌、未明显使用、整车和配件包装齐全的车辆，签收后 7 天内可申请无理由退换。已上牌车辆、明显磨损车辆或定制改装车辆不适用无理由退换，但可按质量问题流程处理。', '退货,换货,七天无理由,上牌,包装,质量问题', '2026-06-09T00:00:00+00:00'),
  ('保修政策', '整车与电池保修', '电池、电机、控制器分别保修多久？', '悦行整车主要部件保修 12 个月，电机和控制器保修 24 个月，原装锂电池保修 36 个月。人为进水、私自改装、非原厂充电器导致的损坏不在免费保修范围内。', '保修,质保,电池,电机,控制器,进水,改装', '2026-06-09T00:00:00+00:00'),
  ('故障排查', '车辆无法启动', '车子无法启动应该怎么排查？', '请先检查电量是否充足、空气开关是否打开、刹车把是否回弹、钥匙/NFC 是否解锁成功。如果仪表亮但无法行驶，可能是刹车断电开关或控制器保护；建议拍摄仪表提示并联系门店检测。', '无法启动,启动不了,仪表,刹车,空气开关,NFC,控制器', '2026-06-09T00:00:00+00:00'),
  ('故障排查', '续航明显变短', '续航突然变短是什么原因？', '续航受载重、胎压、温度、骑行速度和电池健康影响。建议先检查胎压、充电器指示灯和 App 电池健康度；冬季低温续航下降 15% 到 30% 属于常见现象。若满电续航低于标称 50%，建议预约检测。', '续航,变短,电池,胎压,低温,充电器,检测', '2026-06-09T00:00:00+00:00'),
  ('故障排查', 'App 蓝牙连接失败', '手机 App 连接不上车辆怎么办？', '请确认手机蓝牙和定位权限已开启，车辆处于解锁状态，并在 App 中删除旧绑定后重新搜索。若仍失败，可长按车辆电源键 8 秒重启车机，再靠近车辆 1 米内尝试绑定。', 'App,蓝牙,连接失败,定位,绑定,重启', '2026-06-09T00:00:00+00:00'),
  ('售后服务', '门店维修预约', '如何预约售后维修？', '用户可提供所在城市、车型、故障现象和方便到店时间。系统会推荐最近服务门店，并生成预约单。到店时请携带购车凭证、保修卡或电子订单截图。', '维修,预约,门店,服务网点,保修卡,凭证', '2026-06-09T00:00:00+00:00'),
  ('售后服务', '发票与凭证', '如何开具发票？', '个人用户可在订单完成后 30 天内申请电子普通发票；企业用户需提供抬头、税号和邮箱。发票金额以实付金额为准，优惠券和置换抵扣部分不计入发票金额。', '发票,电子发票,企业,税号,抬头,邮箱', '2026-06-09T00:00:00+00:00'),
  ('客户安抚', '投诉与情绪安抚', '用户对维修慢、物流慢或质量问题很生气时如何回应？', '先表达理解和歉意，再确认订单/车辆信息，给出可执行的下一步和预计时效。若涉及安全、质量争议或多次维修，应升级人工客服，并承诺在 2 小时内回访处理进度。', '投诉,生气,不满意,道歉,升级,人工客服,回访', '2026-06-09T00:00:00+00:00')
ON DUPLICATE KEY UPDATE
  category = VALUES(category),
  title = VALUES(title),
  question = VALUES(question),
  answer = VALUES(answer),
  keywords = VALUES(keywords),
  updated_at = VALUES(updated_at);

INSERT INTO demo_orders
  (order_no, customer_name, product_name, status, logistics_status, payment_status,
   aftersale_status, amount, city, created_at, updated_at)
VALUES
  ('YX202606090001', '演示客户A', '悦行 S1 城市通勤版', '已出库，运输中', '已到达华东转运中心，预计明天到达城市网点', '已支付', '暂未发起售后', 2699.00, '杭州', '2026-06-09T00:00:00+00:00', '2026-06-09T00:00:00+00:00'),
  ('YX202606090002', '演示客户B', '悦行 Pro 家庭长续航版', '门店待自提', '车辆已到店，提车码将在核验手机号后发送', '已支付', '暂未发起售后', 3699.00, '上海', '2026-06-09T00:00:00+00:00', '2026-06-09T00:00:00+00:00'),
  ('YX202606090003', '演示客户C', '悦行 S1 城市通勤版', '售后处理中', '订单已签收，当前进入售后工单流程', '已支付', '门店已受理，预计 2 小时内回访', 2699.00, '南京', '2026-06-09T00:00:00+00:00', '2026-06-09T00:00:00+00:00')
ON DUPLICATE KEY UPDATE
  product_name = VALUES(product_name),
  status = VALUES(status),
  logistics_status = VALUES(logistics_status),
  payment_status = VALUES(payment_status),
  aftersale_status = VALUES(aftersale_status),
  amount = VALUES(amount),
  city = VALUES(city),
  updated_at = VALUES(updated_at);

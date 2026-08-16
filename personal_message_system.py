# personal_message_system.py
# 个人消息系统 - 学生端消息中心
# 支持消息收发、已读未读管理、Word附件上传
# 表结构采用一对多设计：消息内容存一份，接收关系独立存

import pymysql
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from flask import request, jsonify
import os
import uuid
from werkzeug.utils import secure_filename

# ---------- 附件配置 ----------
ALLOWED_EXTENSIONS = {'doc', 'docx'}           # 只允许 Word 文档
MAX_FILE_SIZE = 10 * 1024 * 1024              # 单个文件上限 10MB
UPLOAD_FOLDER = 'uploads/messages'            # 附件存储目录

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """检查文件后缀是否在白名单内"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- 枚举定义 ----------
class MessageType(Enum):
    ASSIGNMENT = "assignment"   # 作业
    NOTICE = "notice"           # 通知
    SYSTEM = "system"           # 系统消息


class MessageStatus(Enum):
    UNREAD = "unread"
    READ = "read"
    DELETED = "deleted"


# ---------- 消息实体 ----------
class Message:
    """消息数据对象，用于在业务层和接口层之间传递"""
    def __init__(
        self,
        message_id: int,
        title: str,
        content: str,
        sender_id: int,
        sender_name: str,
        receiver_id: int,
        message_type: MessageType,
        status: MessageStatus = MessageStatus.UNREAD,
        created_at: Optional[datetime] = None,
        read_at: Optional[datetime] = None,
        deadline: Optional[datetime] = None,
        attachment_url: Optional[str] = None,
        attachment_name: Optional[str] = None,
        attachment_size: Optional[int] = None
    ):
        self.message_id = message_id
        self.title = title
        self.content = content
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.receiver_id = receiver_id
        self.message_type = message_type
        self.status = status
        self.created_at = created_at or datetime.now()
        self.read_at = read_at
        self.deadline = deadline
        self.attachment_url = attachment_url
        self.attachment_name = attachment_name
        self.attachment_size = attachment_size

    def to_dict(self) -> Dict[str, Any]:
        """转成前端需要的 JSON 格式"""
        return {
            "message_id": self.message_id,
            "title": self.title,
            "content": self.content,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type.value,
            "status": self.status.value,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "read_at": self.read_at.strftime("%Y-%m-%d %H:%M:%S") if self.read_at else None,
            "deadline": self.deadline.strftime("%Y-%m-%d %H:%M:%S") if self.deadline else None,
            "attachment_url": self.attachment_url,
            "attachment_name": self.attachment_name,
            "attachment_size": self.attachment_size,
            "is_overdue": self._is_overdue()
        }

    def _is_overdue(self) -> bool:
        """判断作业是否已过截止时间"""
        if self.message_type == MessageType.ASSIGNMENT and self.deadline:
            return datetime.now() > self.deadline
        return False


# ---------- 核心业务类 ----------
class PersonalMessageSystem:
    """消息系统增删改查的入口，所有数据库操作都在这里"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self._init_database()

    def _get_connection(self):
        return pymysql.connect(**self.db_config)

    def _init_database(self):
        """建表。如果表已存在则跳过。"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 消息内容表：存一份
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_content (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    sender_id INT NOT NULL,
                    sender_name VARCHAR(100) NOT NULL,
                    message_type ENUM('assignment', 'notice', 'system') NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deadline TIMESTAMP NULL,
                    attachment_url VARCHAR(500),
                    attachment_name VARCHAR(255),
                    attachment_size INT,
                    INDEX idx_created (created_at),
                    INDEX idx_deadline (deadline)
                )
            """)

            # 接收关系表：记录谁收到了哪条消息
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_receiver (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    message_id INT NOT NULL,
                    receiver_id INT NOT NULL,
                    status ENUM('unread', 'read', 'deleted') DEFAULT 'unread',
                    read_at TIMESTAMP NULL,
                    INDEX idx_message (message_id),
                    INDEX idx_receiver (receiver_id),
                    INDEX idx_receiver_status (receiver_id, status),
                    FOREIGN KEY (message_id) REFERENCES message_content(id) ON DELETE CASCADE
                )
            """)

            conn.commit()
            print("消息表初始化完成（一对多结构）")

        except Exception as e:
            print(f"建表失败: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    # ---------- 发送消息（支持批量） ----------
    def send_message(
        self,
        title: str,
        content: str,
        sender_id: int,
        sender_name: str,
        receiver_ids: List[int],
        message_type: str = "assignment",
        deadline: Optional[str] = None,
        attachment_url: Optional[str] = None,
        attachment_name: Optional[str] = None,
        attachment_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        发送消息，支持一次发给多个学生。
        receiver_ids 传列表，如 [1001, 1002, 1003]
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 解析截止时间
            deadline_dt = None
            if deadline:
                for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                    try:
                        deadline_dt = datetime.strptime(deadline, fmt)
                        break
                    except ValueError:
                        continue
                if deadline_dt is None:
                    return {"success": False, "error": "截止时间格式错误，请用 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS"}

            # 1. 插入消息内容
            cursor.execute("""
                INSERT INTO message_content 
                (title, content, sender_id, sender_name, message_type, deadline, 
                 attachment_url, attachment_name, attachment_size)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, content, sender_id, sender_name, message_type,
                  deadline_dt, attachment_url, attachment_name, attachment_size))
            message_id = cursor.lastrowid

            # 2. 批量插入接收关系
            for rid in receiver_ids:
                cursor.execute(
                    "INSERT INTO message_receiver (message_id, receiver_id) VALUES (%s, %s)",
                    (message_id, rid)
                )

            conn.commit()
            return {
                "success": True,
                "message": f"已发送给 {len(receiver_ids)} 名学生",
                "message_id": message_id,
                "receiver_count": len(receiver_ids)
            }

        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            conn.close()

    # ---------- 获取某学生的消息列表 ----------
    def get_user_messages(
        self,
        user_id: int,
        filter_type: str = "all",
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        查某个学生收到的消息。
        filter_type: all / unread / assignments / notices
        """
        conn = self._get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        try:
            sql = """
                SELECT 
                    c.id as message_id,
                    c.title,
                    c.content,
                    c.sender_id,
                    c.sender_name,
                    c.message_type,
                    c.created_at,
                    c.deadline,
                    c.attachment_url,
                    c.attachment_name,
                    c.attachment_size,
                    r.receiver_id,
                    r.status,
                    r.read_at
                FROM message_receiver r
                JOIN message_content c ON r.message_id = c.id
                WHERE r.receiver_id = %s AND r.status != 'deleted'
            """
            params = [user_id]

            if filter_type == "unread":
                sql += " AND r.status = 'unread'"
            elif filter_type == "assignments":
                sql += " AND c.message_type = 'assignment'"
            elif filter_type == "notices":
                sql += " AND c.message_type IN ('notice', 'system')"

            sql += " ORDER BY c.created_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            messages = []
            for row in rows:
                msg = Message(
                    message_id=row['message_id'],
                    title=row['title'],
                    content=row['content'],
                    sender_id=row['sender_id'],
                    sender_name=row['sender_name'],
                    receiver_id=row['receiver_id'],
                    message_type=MessageType(row['message_type']),
                    status=MessageStatus(row['status']),
                    created_at=row['created_at'],
                    read_at=row['read_at'],
                    deadline=row['deadline'],
                    attachment_url=row['attachment_url'],
                    attachment_name=row['attachment_name'],
                    attachment_size=row['attachment_size']
                )
                messages.append(msg)

            stats = self._get_message_statistics(user_id, conn)

            return {
                "success": True,
                "messages": [m.to_dict() for m in messages],
                "statistics": stats
            }

        except Exception as e:
            return {"success": False, "error": str(e), "messages": [], "statistics": {}}
        finally:
            cursor.close()
            conn.close()

    # ---------- 统计信息 ----------
    def _get_message_statistics(self, user_id: int, conn) -> Dict[str, Any]:
        """拉一下总数、未读数、作业数这些统计值"""
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM message_receiver WHERE receiver_id = %s AND status != 'deleted'",
                (user_id,)
            )
            total = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM message_receiver WHERE receiver_id = %s AND status = 'unread'",
                (user_id,)
            )
            unread = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM message_receiver r
                JOIN message_content c ON r.message_id = c.id
                WHERE r.receiver_id = %s AND r.status != 'deleted' AND c.message_type = 'assignment'
            """, (user_id,))
            assignments = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM message_receiver r
                JOIN message_content c ON r.message_id = c.id
                WHERE r.receiver_id = %s AND r.status = 'unread' AND c.message_type = 'assignment'
            """, (user_id,))
            unread_assignments = cursor.fetchone()[0]

            return {
                "total": total,
                "unread": unread,
                "assignments": assignments,
                "unread_assignments": unread_assignments
            }
        except Exception:
            return {}
        finally:
            cursor.close()

    # ---------- 消息摘要（给小红点用） ----------
    def get_message_summary(self, user_id: int) -> Dict[str, Any]:
        """只返回未读总数和未读作业数，前端用来显示小红点"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM message_receiver WHERE receiver_id = %s AND status = 'unread'",
                (user_id,)
            )
            unread_total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM message_receiver r
                JOIN message_content c ON r.message_id = c.id
                WHERE r.receiver_id = %s AND r.status = 'unread' AND c.message_type = 'assignment'
            """, (user_id,))
            unread_assignments = cursor.fetchone()[0]

            return {
                "success": True,
                "data": {
                    "unread_total": unread_total,
                    "unread_assignments": unread_assignments,
                    "has_unread": unread_total > 0
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            conn.close()

    # ---------- 标记已读 ----------
    def mark_as_read(self, message_id: int, user_id: int) -> Dict[str, Any]:
        """把某条消息标为已读"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE message_receiver 
                SET status = 'read', read_at = NOW() 
                WHERE message_id = %s AND receiver_id = %s AND status = 'unread'
            """, (message_id, user_id))
            conn.commit()
            if cursor.rowcount > 0:
                return {"success": True, "message": "已标记已读"}
            return {"success": False, "message": "消息不存在或已经是已读状态"}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            conn.close()

    def mark_all_as_read(self, user_id: int) -> Dict[str, Any]:
        """一键全部已读"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE message_receiver SET status = 'read', read_at = NOW() WHERE receiver_id = %s AND status = 'unread'",
                (user_id,)
            )
            conn.commit()
            return {"success": True, "message": f"已标记 {cursor.rowcount} 条消息为已读"}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            conn.close()

    # ---------- 删除 ----------
    def delete_message(self, message_id: int, user_id: int) -> Dict[str, Any]:
        """删除某条消息（只改状态，不删物理记录）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE message_receiver SET status = 'deleted' WHERE message_id = %s AND receiver_id = %s",
                (message_id, user_id)
            )
            conn.commit()
            if cursor.rowcount > 0:
                return {"success": True, "message": "已删除"}
            return {"success": False, "message": "消息不存在"}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            conn.close()

    def delete_all_read(self, user_id: int) -> Dict[str, Any]:
        """一键清空已读消息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE message_receiver SET status = 'deleted' WHERE receiver_id = %s AND status = 'read'",
                (user_id,)
            )
            conn.commit()
            return {"success": True, "message": f"已删除 {cursor.rowcount} 条已读消息"}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            cursor.close()
            conn.close()

    # ---------- 测试数据 ----------
    def add_test_messages(self, user_id: int):
        """往数据库塞几条测试消息，方便开发时调试"""
        test_data = [
            {
                "title": "【作业】动态规划专题练习",
                "content": "背包问题 + 最长公共子序列，共5题",
                "sender_id": 1001,
                "sender_name": "张老师",
                "message_type": "assignment",
                "deadline": datetime.now().replace(day=28, hour=23, minute=59).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "title": "【通知】算法竞赛训练营",
                "content": "本周六上午9点开营",
                "sender_id": 0,
                "sender_name": "系统管理员",
                "message_type": "notice",
                "deadline": None
            },
            {
                "title": "【作业】图论算法练习",
                "content": "最短路径 + 最小生成树",
                "sender_id": 1001,
                "sender_name": "李老师",
                "message_type": "assignment",
                "deadline": datetime.now().replace(day=25, hour=23, minute=59).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]

        for item in test_data:
            self.send_message(
                title=item["title"],
                content=item["content"],
                sender_id=item["sender_id"],
                sender_name=item["sender_name"],
                receiver_ids=[user_id],
                message_type=item["message_type"],
                deadline=item["deadline"]
            )
        print(f"已为用户 {user_id} 添加 {len(test_data)} 条测试消息")


# ---------- 附件上传 ----------
def save_uploaded_file(file) -> Dict[str, Any]:
    """保存上传的 Word 文件，返回存储信息"""
    if not file:
        return {"success": False, "error": "没有文件"}

    if file.filename == '':
        return {"success": False, "error": "文件名为空"}

    if not allowed_file(file.filename):
        return {"success": False, "error": "仅支持 .doc 和 .docx 格式"}

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return {"success": False, "error": f"文件超过 {MAX_FILE_SIZE // (1024*1024)}MB 限制"}

    original_name = secure_filename(file.filename)
    ext = original_name.rsplit('.', 1)[1].lower()
    new_name = f"{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(UPLOAD_FOLDER, new_name)

    try:
        file.save(save_path)
        return {
            "success": True,
            "file_path": f"/uploads/messages/{new_name}",
            "file_name": original_name,
            "file_size": file_size
        }
    except Exception as e:
        return {"success": False, "error": f"保存失败: {str(e)}"}


# ---------- 全局变量 ----------
message_system = None


def init_message_system(db_config):
    global message_system
    message_system = PersonalMessageSystem(db_config)
    return message_system


# ---------- 路由注册 ----------
def create_message_routes(app):
    """把所有消息相关的路由挂到 Flask app 上"""

    @app.route('/api-py/get_messages', methods=['GET'])
    def get_messages():
        user_id = request.args.get('id', type=int)
        filter_type = request.args.get('filter', 'all')
        if not user_id:
            return jsonify({'success': False, 'error': '缺少 user_id'}), 400
        return jsonify(message_system.get_user_messages(user_id, filter_type))

    @app.route('/api-py/mark_read/<int:message_id>', methods=['POST'])
    def mark_read(message_id):
        data = request.get_json() or {}
        user_id = data.get('user_id') or request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'success': False, 'error': '缺少 user_id'}), 400
        return jsonify(message_system.mark_as_read(message_id, user_id))

    @app.route('/api-py/mark_all_read', methods=['POST'])
    def mark_all_read():
        data = request.get_json() or {}
        user_id = data.get('user_id') or request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'success': False, 'error': '缺少 user_id'}), 400
        return jsonify(message_system.mark_all_as_read(user_id))

    @app.route('/api-py/delete_message/<int:message_id>', methods=['DELETE'])
    def delete_message(message_id):
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'success': False, 'error': '缺少 user_id'}), 400
        return jsonify(message_system.delete_message(message_id, user_id))

    @app.route('/api-py/delete_all_read', methods=['DELETE'])
    def delete_all_read():
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'success': False, 'error': '缺少 user_id'}), 400
        return jsonify(message_system.delete_all_read(user_id))

    @app.route('/api-py/message_summary', methods=['GET'])
    def message_summary():
        user_id = request.args.get('id', type=int)
        if not user_id:
            return jsonify({'success': False, 'error': '缺少 user_id'}), 400
        return jsonify(message_system.get_message_summary(user_id))

    @app.route('/api-py/add_test_messages', methods=['POST'])
    def add_test_messages():
        user_id = request.json.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': '缺少 user_id'}), 400
        message_system.add_test_messages(user_id)
        return jsonify({'success': True, 'message': '测试消息已添加'})

    # ---------- 文件上传 ----------
    @app.route('/api-py/upload_attachment', methods=['POST'])
    def upload_attachment():
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400
        result = save_uploaded_file(request.files['file'])
        if result['success']:
            return jsonify({
                'success': True,
                'data': {
                    'file_url': result['file_path'],
                    'file_name': result['file_name'],
                    'file_size': result['file_size']
                }
            })
        return jsonify({'success': False, 'error': result['error']}), 400

    @app.route('/api-py/upload_attachment_with_message', methods=['POST'])
    def upload_attachment_with_message():
        """上传附件 + 发送消息 二合一接口，教师端直接用"""
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'}), 400

        required = ['title', 'content', 'sender_id', 'sender_name', 'receiver_ids']
        for f in required:
            if f not in request.form:
                return jsonify({'success': False, 'error': f'缺少字段: {f}'}), 400

        # 保存附件
        upload_result = save_uploaded_file(request.files['file'])
        if not upload_result['success']:
            return jsonify({'success': False, 'error': upload_result['error']}), 400

        # 解析 receiver_ids：支持 JSON 或逗号分隔
        raw = request.form.get('receiver_ids')
        try:
            receiver_ids = json.loads(raw)
        except:
            receiver_ids = [int(x.strip()) for x in raw.split(',')]

        if not receiver_ids:
            return jsonify({'success': False, 'error': 'receiver_ids 不能为空'}), 400

        # 调用发送
        result = message_system.send_message(
            title=request.form.get('title'),
            content=request.form.get('content'),
            sender_id=request.form.get('sender_id', type=int),
            sender_name=request.form.get('sender_name'),
            receiver_ids=receiver_ids,
            message_type=request.form.get('message_type', 'assignment'),
            deadline=request.form.get('deadline'),
            attachment_url=upload_result['file_path'],
            attachment_name=upload_result['file_name'],
            attachment_size=upload_result['file_size']
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'message_id': result['message_id'],
                    'receiver_count': result['receiver_count'],
                    'attachment': {
                        'file_url': upload_result['file_path'],
                        'file_name': upload_result['file_name']
                    }
                }
            })
        return jsonify({'success': False, 'error': result['error']}), 400

    print("消息路由注册完成")
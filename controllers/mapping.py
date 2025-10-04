from flask import Blueprint, request, jsonify
import mysql.connector
from datetime import datetime

mapping_bp = Blueprint("mapping", __name__, url_prefix="/api/mapping")

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'wlsdud0802!!',  # 본인 MySQL 비밀번호
    'database': 'clara_cs',
    'auth_plugin': 'mysql_native_password'
}

# ✅ 매핑 저장 API
@mapping_bp.route("/save", methods=["POST"])
def save_mapping():
    data = request.get_json()

    try:
        # ✅ MySQL 연결
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # ✅ created_at 처리
        created_at_str = data.get('created_at')
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                created_at_str = created_at.strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print("Date parsing error:", e)
                created_at_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            created_at_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ✅ INSERT 쿼리 실행
        insert_query = """
            INSERT INTO tb_column_mapping (original_column, file_id, mapping_code_id, is_activate, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        for m in data.get('mappings', []):
            # 각 항목별로 created_at 생성
            created_at_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(insert_query, (
                m.get('original_column'),
                m.get('file_id'),
                m.get('mapping_code_id'),
                m.get('is_activate'),
                created_at_str
            ))

        conn.commit()

        return jsonify({'status': 'success', 'message': 'Mapping saved successfully'})

    except Exception as e:
        print("DB Error:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ✅ 마지막 매핑 가져오기 API
@mapping_bp.route("/last", methods=['GET'])
def get_last_mapping():
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # tb_column_mapping 테이블 존재 여부 체크
        cursor.execute("""
            SELECT COUNT(*) AS cnt 
            FROM information_schema.tables 
            WHERE table_schema=%s AND table_name='tb_column_mapping'
        """, (DB_CONFIG['database'],))
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            print("테이블이 존재하지 않습니다: tb_column_mapping")
            return jsonify({'mappings': [], 'msg': '테이블 없음'})

        # 실제 매핑 데이터 조회
        cursor.execute("SELECT * FROM tb_column_mapping ORDER BY created_at DESC")
        rows = cursor.fetchall()  # dictionary=True이면 dict 반환

        return jsonify({'mappings': rows})

    except Exception as e:
        print("DB Error:", e)
        return jsonify({'mappings': [], 'msg': str(e)})
    
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
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

# ✅ 매핑 저장 API (안정화 버전)
@mapping_bp.route("/save", methods=["POST"])
def save_mapping():
    try:
        data = request.get_json(force=True)
        if not data or "mappings" not in data:
            return jsonify({'status': 'error', 'message': '잘못된 요청입니다.'}), 400

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # ✅ INSERT 쿼리
        insert_query = """
            INSERT INTO tb_column_mapping (original_column, file_id, mapping_code_id, is_activate, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """

        for m in data.get('mappings', []):
            original_column = m.get('original_column')
            file_id = m.get('file_id')
            mapping_code_id = m.get('mapping_code_id')
            is_activate = m.get('is_activate', 1)
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # ✅ 필수값 체크
            if not original_column or not file_id:
                continue

            cursor.execute(insert_query, (
                original_column,
                file_id,
                mapping_code_id,
                is_activate,
                created_at
            ))

        conn.commit()

        return jsonify({'status': 'success', 'message': 'Mapping saved successfully'}), 200

    except mysql.connector.Error as db_err:
        print("[MySQL Error]", db_err)
        return jsonify({'status': 'error', 'message': f"MySQL 오류: {str(db_err)}"}), 500

    except Exception as e:
        print("[Server Error]", e)
        return jsonify({'status': 'error', 'message': f"서버 오류: {str(e)}"}), 500

    finally:
        try:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn.is_connected():
                conn.close()
        except Exception as close_err:
            print("[Close Error]", close_err)


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
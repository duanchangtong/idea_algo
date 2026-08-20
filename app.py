"""痛点收集平台 - Flask后端"""
import webbrowser
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
from config import Config
import models

app = Flask(__name__)
CORS(app)

# 初始化数据库
models.init_db()

# 初始化AI客户端
ai_client = None
if Config.BAILIAN_API_KEY:
    ai_client = OpenAI(
        api_key=Config.BAILIAN_API_KEY,
        base_url=Config.BAILIAN_BASE_URL,
    )


def get_ai_suggestion(scene: str, pain_point: str, desired_effect: str) -> str:
    """调用Qwen模型生成AI建议"""
    if not ai_client:
        return ""
    try:
        prompt = f"""你是一个具身智能与生活体验创新顾问。用户描述了在现实物理环境中感知到的不便或想要改善的体验（如做事流程、交互方式、服务体验等），请给出简短实用的改进建议或未来可能的解决方案（100字以内）。

场景：{scene}
痛点/不舒服的地方：{pain_point}
期望体验：{desired_effect}

请直接给出建议，不要加前缀。"""
        resp = ai_client.chat.completions.create(
            model=Config.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI调用失败: {e}")
        return ""


# ==================== 页面路由 ====================

@app.route("/")
def index():
    return render_template("index.html")


# ==================== API路由 ====================

@app.route("/api/register", methods=["POST"])
def register():
    """用户注册（简化版，昵称即可）"""
    data = request.json
    nickname = data.get("nickname", "").strip()
    avatar = data.get("avatar", "😊")
    if not nickname:
        return jsonify({"error": "昵称不能为空"}), 400
    user = models.create_user(nickname, avatar)
    return jsonify(user)


@app.route("/api/user/<user_id>")
def get_user(user_id):
    """获取用户信息"""
    user = models.get_user(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    return jsonify(user)


@app.route("/api/ideas", methods=["GET"])
def list_ideas():
    """获取点子列表"""
    category = request.args.get("category", "")
    sort_by = request.args.get("sort", "latest")
    page = int(request.args.get("page", 1))
    ideas = models.get_ideas(category=category, sort_by=sort_by, page=page)
    return jsonify(ideas)


@app.route("/api/ideas", methods=["POST"])
def create_idea():
    """提交新点子"""
    data = request.json
    user_id = data.get("user_id", "")
    scene = data.get("scene", "").strip()
    pain_point = data.get("pain_point", "").strip()
    desired_effect = data.get("desired_effect", "").strip()
    category = data.get("category", "其他")
    emotion = data.get("emotion", "")
    location = data.get("location", "").strip()

    if not user_id or not scene or not pain_point or not desired_effect:
        return jsonify({"error": "请填写完整信息"}), 400

    user = models.get_user(user_id)
    if not user:
        return jsonify({"error": "用户不存在"}), 404

    # 调用AI生成建议
    ai_suggestion = get_ai_suggestion(scene, pain_point, desired_effect)

    idea = models.create_idea(
        user_id=user_id,
        category=category,
        scene=scene,
        pain_point=pain_point,
        desired_effect=desired_effect,
        emotion=emotion,
        location=location,
        ai_suggestion=ai_suggestion,
    )
    return jsonify(idea)


@app.route("/api/ideas/<idea_id>")
def idea_detail(idea_id):
    """获取点子详情"""
    idea = models.get_idea_detail(idea_id)
    if not idea:
        return jsonify({"error": "点子不存在"}), 404
    return jsonify(idea)


@app.route("/api/ideas/<idea_id>/like", methods=["POST"])
def like_idea(idea_id):
    """点赞/取消点赞"""
    data = request.json
    user_id = data.get("user_id", "")
    if not user_id:
        return jsonify({"error": "请先登录"}), 401
    result = models.toggle_like(idea_id, user_id)
    return jsonify(result)


@app.route("/api/ideas/<idea_id>/liked")
def check_liked(idea_id):
    """检查是否已点赞"""
    user_id = request.args.get("user_id", "")
    liked = models.has_liked(idea_id, user_id)
    return jsonify({"liked": liked})


@app.route("/api/leaderboard")
def leaderboard():
    """排行榜"""
    limit = int(request.args.get("limit", 10))
    data = models.get_leaderboard(limit)
    return jsonify(data)


@app.route("/api/stats")
def stats():
    """平台统计"""
    return jsonify(models.get_stats())


@app.route("/api/reward-tiers")
def reward_tiers():
    """获取奖励阶梯配置"""
    return jsonify(Config.REWARD_TIERS)


# ==================== 同感（我也遇到了）====================

@app.route("/api/ideas/<idea_id>/empathy", methods=["POST"])
def empathy_idea(idea_id):
    """表示同感/取消同感"""
    data = request.json
    user_id = data.get("user_id", "")
    if not user_id:
        return jsonify({"error": "请先登录"}), 401
    result = models.toggle_empathy(idea_id, user_id)
    return jsonify(result)


# ==================== 轻评论 ====================

@app.route("/api/ideas/<idea_id>/comments", methods=["GET"])
def list_comments(idea_id):
    """获取评论列表"""
    comments = models.get_comments(idea_id)
    return jsonify(comments)


@app.route("/api/ideas/<idea_id>/comments", methods=["POST"])
def add_comment(idea_id):
    """添加评论（限50字）"""
    data = request.json
    user_id = data.get("user_id", "")
    content = data.get("content", "").strip()
    if not user_id:
        return jsonify({"error": "请先登录"}), 401
    if not content:
        return jsonify({"error": "评论内容不能为空"}), 400
    if len(content) > 50:
        return jsonify({"error": "评论不能超过50字"}), 400
    comment = models.add_comment(idea_id, user_id, content)
    return jsonify(comment)


# ==================== 每日随机痛点 ====================

@app.route("/api/random-idea")
def random_idea():
    """随机获取一条点子"""
    idea = models.get_random_idea()
    if not idea:
        return jsonify({"empty": True})
    return jsonify(idea)


# ==================== 痛点热区 ====================

@app.route("/api/location-stats")
def location_stats():
    """按地点统计痛点"""
    data = models.get_location_stats()
    return jsonify(data)


if __name__ == "__main__":
    print("=" * 50)
    print("  痛点收集平台已启动")
    print("  访问: http://127.0.0.1:5000")
    print("=" * 50)
    # 自动打开浏览器
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)

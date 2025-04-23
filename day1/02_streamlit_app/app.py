# app.py
import streamlit as st
import ui                   # UIモジュール
from llm import load_model  # LLMモジュール
import database             # データベースモジュール
import metrics              # 評価指標モジュール
import data                 # データモジュール
import torch
from transformers import pipeline
from config import MODEL_GEMMA, MODEL_SB
from huggingface_hub import HfFolder

# --- アプリケーション設定 ---
st.set_page_config(page_title="Gemma / SB Intuitions  Chatbot", layout="wide")


# --- （追加）モデル選択 ---
MODEL_OPTIONS = {
    "google/gemma-2-2b-jpn-it": MODEL_GEMMA,
    "sbintuitions/sarashina2.2-1b-instruct-v0.1": MODEL_SB,
}

# （追加）モデル選択用サイドバー
st.sidebar.title("ナビゲーション")
selected_model_label = st.sidebar.selectbox(
    "使用するモデルを選択",
    list(MODEL_OPTIONS.keys()),
    index=0,
)
MODEL_NAME = MODEL_OPTIONS[selected_model_label]

st.sidebar.markdown(f"**現在のモデル:** `{MODEL_NAME}`")


# --- 初期化処理 ---
# NLTKデータのダウンロード（初回起動時など）
metrics.initialize_nltk()

# データベースの初期化（テーブルが存在しない場合、作成）
database.init_db()

# データベースが空ならサンプルデータを投入
data.ensure_initial_data()

# LLMモデルのロード（キャッシュを利用）
# モデルをキャッシュして再利用
@st.cache_resource(show_spinner="モデルをロード中です…")
def load_model(model_name: str):
    """指定された model_name をロードして返す。キャッシュされる。"""
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        st.info(f"Using device: {device}")  # 使用デバイスを表示

        pipe = pipeline(
            "text-generation",
            model=model_name,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device=device,
        )
        st.success(f"モデル '{model_name}' の読み込みに成功しました。")
        return pipe
    except Exception as e:
        st.error(f"モデル '{model_name}' の読み込みに失敗しました: {e}")
        st.error("GPUメモリ不足の可能性があります。不要なプロセスを終了するか、より小さいモデルの使用を検討してください。")
        return None
pipe = load_model(MODEL_NAME)

# --- Streamlit アプリケーション ---
st.title("🤖 Gemma / SB Intuitions  Chatbot with Feedback")
st.write("Gemma / SB Intuitions  モデルを使用したチャットボットです。回答に対してフィードバックを行えます。")
st.markdown("---")

# --- サイドバー ---
st.sidebar.title("ナビゲーション")
# セッション状態を使用して選択ページを保持
if 'page' not in st.session_state:
    st.session_state.page = "チャット" # デフォルトページ

page = st.sidebar.radio(
    "ページ選択",
    ["チャット", "履歴閲覧", "サンプルデータ管理"],
    key="page_selector",
    index=["チャット", "履歴閲覧", "サンプルデータ管理"].index(st.session_state.page), # 現在のページを選択状態にする
    on_change=lambda: setattr(st.session_state, 'page', st.session_state.page_selector) # 選択変更時に状態を更新
)


# --- メインコンテンツ ---
if st.session_state.page == "チャット":
    if pipe:
        ui.display_chat_page(pipe)
    else:
        st.error("チャット機能を利用できません。モデルの読み込みに失敗しました。")
elif st.session_state.page == "履歴閲覧":
    ui.display_history_page()
elif st.session_state.page == "サンプルデータ管理":
    ui.display_data_page()


# --- フッターなど（任意） ---
st.sidebar.markdown("---")
st.sidebar.info("開発者: Shibayuuuu")
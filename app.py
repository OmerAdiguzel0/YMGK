"""LGS Kareköklü İfadeler Soru Üretim Arayüzü - Streamlit"""

import json
import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Proje root'unu path'e ekle
sys.path.insert(0, str(Path(__file__).parent))

from src.models.question_generator import QuestionGenerator
from src.pipelines.predict_similarity import find_similar_questions


# Sayfa yapılandırması
st.set_page_config(
    page_title="LGS Kareköklü İfadeler Soru Üretim",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stilleri
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        padding-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .question-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_generator():
    """Soru üretici modelini yükle."""
    model_dir = Path("models/baseline")
    generator = QuestionGenerator()
    
    templates_path = model_dir / "templates.json"
    if templates_path.exists():
        generator.load_templates(templates_path)
    
    return generator


@st.cache_data
def load_questions():
    """Mevcut soruları yükle."""
    questions_path = Path("models/baseline/questions.json")
    if questions_path.exists():
        with questions_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return []


def main():
    # Başlık
    st.markdown('<h1 class="main-header">📚 LGS Kareköklü İfadeler Soru Üretim Sistemi</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Yapay Zeka ile Kareköklü İfadeler Soruları Üretin ve Benzer Soruları Bulun</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Ayarlar")
        
        # Model durumu
        st.subheader("📊 Model Durumu")
        model_dir = Path("models/baseline")
        
        has_templates = (model_dir / "templates.json").exists()
        has_questions = (model_dir / "questions.json").exists()
        has_vectorizer = (model_dir / "vectorizer.joblib").exists()
        
        st.success("✓ Şablonlar yüklü" if has_templates else "✗ Şablonlar yok")
        st.success("✓ Sorular yüklü" if has_questions else "✗ Sorular yok")
        st.success("✓ Benzerlik modeli yüklü" if has_vectorizer else "✗ Benzerlik modeli yok")
        
        st.divider()
        
        # İstatistikler
        st.subheader("📈 İstatistikler")
        questions = load_questions()
        if questions:
            st.metric("Toplam Soru", len(questions))
            
            # Kaynaklara göre dağılım
            sources = {}
            for q in questions:
                source = q.get("source_file", "unknown")
                sources[source] = sources.get(source, 0) + 1
            
            st.write("**Kaynaklar:**")
            for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                st.write(f"- {source}: {count} soru")
    
    # Ana içerik
    tab1, tab2, tab3 = st.tabs(["🎲 Soru Üret", "🔍 Benzer Soruları Bul", "📚 Veri Seti"])
    
    # Tab 1: Soru Üret
    with tab1:
        st.header("🎲 Yeni Soru Üret")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            num_questions = st.slider("Üretilecek Soru Sayısı", 1, 20, 5)
            method = st.selectbox(
                "Üretim Yöntemi", 
                ["original", "template", "hybrid"],
                index=0,
                help="original: Orijinal sorulardan varyasyon (önerilen), template: Şablon tabanlı, hybrid: Her ikisi"
            )
        
        with col2:
            st.write("")
            st.write("")
            generate_btn = st.button("🚀 Soru Üret", type="primary", use_container_width=True)
        
        if generate_btn:
            with st.spinner("Sorular üretiliyor..."):
                try:
                    generator = load_generator()
                    
                    questions = load_questions()
                    
                    if method in ["original", "hybrid"] and not questions:
                        st.error("❌ Sorular yüklenemedi! Lütfen önce modeli eğitin.")
                    elif method == "template" and not generator.templates:
                        st.error("❌ Şablonlar yüklenemedi! Lütfen önce modeli eğitin.")
                    else:
                        generated = generator.generate_questions(
                            num_questions=num_questions,
                            method=method,
                            seed_questions=questions if questions else None
                        )
                        
                        st.success(f"✅ {len(generated)} soru başarıyla üretildi!")
                        
                        # Üretilen soruları göster
                        for i, q in enumerate(generated, 1):
                            with st.container():
                                st.markdown(f"### Soru {i}")
                                
                                # Düzenlenebilir metin alanı
                                edited_text = st.text_area(
                                    f"Soru {i} Metni",
                                    value=q['question_text'],
                                    height=100,
                                    key=f"edit_{i}",
                                    help="Soruyu buradan düzenleyebilirsiniz"
                                )
                                
                                # Düzenlenmiş versiyonu güncelle
                                if edited_text != q['question_text']:
                                    q['question_text'] = edited_text
                                    q['edited'] = True
                                
                                st.caption(f"**Yöntem:** {q.get('generation_method', 'unknown')}")
                                
                                # İndirme butonu
                                st.download_button(
                                    label=f"📥 Soru {i}'i İndir",
                                    data=json.dumps(q, ensure_ascii=False, indent=2),
                                    file_name=f"soru_{i}.json",
                                    mime="application/json",
                                    key=f"download_{i}"
                                )
                                
                                st.divider()
                        
                        # Toplu indirme
                        st.download_button(
                            label="📥 Tüm Soruları İndir (JSON)",
                            data=json.dumps(generated, ensure_ascii=False, indent=2),
                            file_name="uretilen_sorular.json",
                            mime="application/json"
                        )
                        
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
                    st.exception(e)
    
    # Tab 2: Benzer Soruları Bul
    with tab2:
        st.header("🔍 Benzer Soruları Bul")
        
        question_input = st.text_area(
            "Soru Metni",
            placeholder="Örnek: Aşağıdaki sayılardan hangisi tam kare sayıdır?",
            height=100
        )
        
        col1, col2 = st.columns([1, 1])
        with col1:
            top_k = st.slider("Gösterilecek Benzer Soru Sayısı", 1, 10, 5)
        with col2:
            st.write("")
            st.write("")
            search_btn = st.button("🔍 Ara", type="primary", use_container_width=True)
        
        if search_btn:
            if not question_input.strip():
                st.warning("⚠️ Lütfen bir soru metni girin!")
            else:
                with st.spinner("Benzer sorular aranıyor..."):
                    try:
                        model_dir = Path("models/baseline")
                        
                        if not (model_dir / "vectorizer.joblib").exists():
                            st.error("❌ Benzerlik modeli bulunamadı!")
                        else:
                            # Benzer soruları bul (Streamlit için özel versiyon)
                            import joblib
                            from sklearn.metrics.pairwise import cosine_similarity
                            
                            vectorizer = joblib.load(model_dir / "vectorizer.joblib")
                            question_vectors = joblib.load(model_dir / "question_vectors.joblib")
                            
                            with (model_dir / "questions.json").open("r", encoding="utf-8") as f:
                                all_questions = json.load(f)
                            
                            question_vector = vectorizer.transform([question_input])
                            similarities = cosine_similarity(question_vector, question_vectors).flatten()
                            top_indices = similarities.argsort()[-top_k:][::-1]
                            
                            st.success(f"✅ {len(top_indices)} benzer soru bulundu!")
                            
                            for i, idx in enumerate(top_indices, 1):
                                sim_score = similarities[idx]
                                q = all_questions[idx]
                                
                                st.markdown(f"""
                                <div class="question-card">
                                    <h4>Benzerlik: {sim_score:.3f}</h4>
                                    <p><strong>Soru:</strong> {q.get('full_text', q.get('raw_text', ''))[:300]}...</p>
                                    <small><strong>Kaynak:</strong> {q.get('source_file', 'unknown')} | 
                                    <strong>Soru No:</strong> {q.get('question_number', 'N/A')}</small>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                st.divider()
                                
                    except Exception as e:
                        st.error(f"❌ Hata: {str(e)}")
                        st.exception(e)
    
    # Tab 3: Veri Seti
    with tab3:
        st.header("📚 Veri Seti Bilgileri")
        
        questions = load_questions()
        
        if questions:
            # Genel istatistikler
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Toplam Soru", len(questions))
            
            with col2:
                sources = set(q.get("source_file", "unknown") for q in questions)
                st.metric("Kaynak Dosya", len(sources))
            
            with col3:
                has_options = sum(1 for q in questions if q.get("options"))
                st.metric("Seçenekli Soru", has_options)
            
            with col4:
                hybrid_count = sum(1 for q in questions if q.get("extraction_method") == "hybrid")
                st.metric("Hybrid Çıkarma", hybrid_count)
            
            st.divider()
            
            # Kaynaklara göre dağılım
            st.subheader("📊 Kaynaklara Göre Dağılım")
            sources_dict = {}
            for q in questions:
                source = q.get("source_file", "unknown")
                sources_dict[source] = sources_dict.get(source, 0) + 1
            
            source_df = pd.DataFrame(list(sources_dict.items()), columns=["Kaynak", "Soru Sayısı"])
            source_df = source_df.sort_values("Soru Sayısı", ascending=False)
            st.bar_chart(source_df.set_index("Kaynak"))
            
            # Örnek sorular
            st.subheader("📝 Örnek Sorular")
            sample_size = st.slider("Gösterilecek Soru Sayısı", 1, min(10, len(questions)), 5)
            
            sample_questions = questions[:sample_size]
            for i, q in enumerate(sample_questions, 1):
                with st.expander(f"Soru {i} - {q.get('source_file', 'unknown')}"):
                    st.write("**Tam Metin:**")
                    st.write(q.get("full_text", q.get("raw_text", "N/A")))
                    
                    if q.get("options"):
                        st.write("**Seçenekler:**")
                        options = q.get("options", [])
                        if isinstance(options, str):
                            st.write(options)
                        else:
                            for opt in options:
                                st.write(f"- {opt}")
        else:
            st.warning("⚠️ Veri seti yüklenemedi!")


if __name__ == "__main__":
    main()


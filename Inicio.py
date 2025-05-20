import streamlit as st
import requests
import json
import time
import base64
from gtts import gTTS
import io
from fpdf import FPDF
import tempfile

# Configuración de la página
st.set_page_config(
    page_title="Asistente Convivencia CEFA",
    page_icon="👬",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)

# Establecer tema personalizado con los colores del CEFA
st.markdown("""
<style>
    /* Tema claro personalizado con colores CEFA */
    body {
        color: #333333;
        background-color: #f9f9f9;
    }
    .stApp {
        background-color: #f9f9f9;
    }
    
    /* Personalización de inputs y controles */
    .stTextInput>div>div>input {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #dddddd;
    }
    .stSlider>div>div>div {
        color: #333333;
    }
    .stSelectbox>div>div>div {
        background-color: #ffffff;
        color: #333333;
    }
    
    /* Botones con estilo transparente y bordes */
    .stButton>button {
        background-color: transparent !important;
        color: #006D2C !important;
        border: 1px solid #008F39 !important;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: rgba(0, 143, 57, 0.1) !important;
        box-shadow: 0 0 5px rgba(0, 143, 57, 0.3);
    }
    
    /* Ajustes para la barra lateral */
    .css-1d391kg, .css-12oz5g7 {
        background-color: #ffffff;
    }
    
    /* Estilos personalizados para el asistente con colores CEFA */
    .main-header {
        font-size: 2.5rem;
        color: #006D2C;
        text-align: center;
        margin-bottom: 1.5rem;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        border-bottom: 3px solid #FFD700;
        padding-bottom: 10px;
    }
    .subheader {
        font-size: 1.5rem;
        color: #008F39;
        margin-bottom: 1rem;
    }
    .audio-controls {
        display: flex;
        align-items: center;
        margin-top: 10px;
    }
    .footer {
        position: fixed;
        bottom: 0;
        width: 100%;
        background-color: #f0f0f0;
        text-align: center;
        padding: 10px;
        font-size: 0.8rem;
        color: #666666;
        border-top: 3px solid #FFD700;
    }
    
    /* Estilos para la barra lateral */
    .sidebar .sidebar-content h1, 
    .sidebar .sidebar-content h2, 
    .sidebar .sidebar-content h3,
    .css-1outpf7 {
        color: #006D2C !important;
    }
    
    /* Estilo para los mensajes de chat */
    .stChatMessage {
        background-color: #f5f5f5;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
        border-left: 2px solid #008F39;
    }
    .stChatMessage.user {
        background-color: rgba(255, 215, 0, 0.05);
        border-left: 2px solid #FFD700;
    }
    .stChatMessage.assistant {
        background-color: rgba(0, 143, 57, 0.05);
    }
    
    /* Estilo para los mensajes info, error, success */
    .stAlert {
        background-color: #f8f9fa;
        color: #333333;
        border-radius: 4px;
    }
    
    /* Ajustes para expanders y otros widgets */
    .streamlit-expanderHeader {
        background-color: rgba(0, 143, 57, 0.05);
        color: #006D2C;
        border-radius: 4px;
    }
    
    /* Decoraciones con los colores CEFA */
    .cefa-decoration {
        background: linear-gradient(to right, #FFD700 50%, #008F39 50%);
        height: 3px;
        width: 100%;
        margin: 10px 0;
    }
    
    /* Estilo para ejemplos de preguntas con colores CEFA */
    .example-question {
        background-color: rgba(255, 215, 0, 0.05);
        border-left: 3px solid #008F39;
        padding: 10px;
        margin-bottom: 8px;
        border-radius: 4px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .example-question span {
        color: #006D2C;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Función para inicializar variables de sesión
def initialize_session_vars():
    if "is_configured" not in st.session_state:
        st.session_state.is_configured = False
    if "agent_endpoint" not in st.session_state:
        # Endpoint fijo como solicitado
        st.session_state.agent_endpoint = "https://jv2gsa34xn3vov7zosdvagru.agents.do-ai.run"
    if "agent_access_key" not in st.session_state:
        st.session_state.agent_access_key = ""
    if "messages" not in st.session_state:
        st.session_state.messages = []

# Inicializar variables
initialize_session_vars()

# Función para generar audio a partir de texto
def text_to_speech(text):
    try:
        # Crear objeto gTTS (siempre en español y rápido)
        tts = gTTS(text=text, lang='es', slow=False)
        
        # Guardar audio en un buffer en memoria
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Convertir a base64 para reproducir en HTML
        audio_base64 = base64.b64encode(audio_buffer.read()).decode()
        audio_html = f'''
        <div class="audio-controls">
            <audio controls style="height: 40px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                Tu navegador no soporta el elemento de audio.
            </audio>
        </div>
        '''
        return audio_html
    except Exception as e:
        return f"<div style='color: #e53e3e; padding: 8px; background-color: #fff5f5; border-radius: 4px;'>Error al generar audio: {str(e)}</div>"

# Título y logotipo del CEFA (banner con colores institucionales)
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown("<h1 class='main-header'>Asistente Convivencia CEFA</h1>", unsafe_allow_html=True)
    st.markdown("<div class='cefa-decoration'></div>", unsafe_allow_html=True)

# Pantalla de configuración inicial si aún no se ha configurado
if not st.session_state.is_configured:
    st.markdown("<h2 class='subheader'>Acceso al Asistente</h2>", unsafe_allow_html=True)
    
    st.info("Por favor ingresa tu clave de acceso al asistente digital")
    
    # Solo solicitar la clave de acceso
    agent_access_key = st.text_input(
        "Clave de Acceso", 
        type="password",
        placeholder="Ingresa tu clave de acceso al asistente",
        help="Tu clave de acceso para autenticar las solicitudes"
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Iniciar sesión", use_container_width=True):
            if not agent_access_key:
                st.error("Por favor, ingresa la clave de acceso")
            else:
                # Guardar configuración en session_state
                st.session_state.agent_access_key = agent_access_key
                st.session_state.is_configured = True
                st.success("Clave configurada correctamente")
                time.sleep(1)  # Breve pausa para mostrar el mensaje de éxito
                st.rerun()
    
    # Parar ejecución hasta que se configure
    st.stop()

# Una vez configurado, mostrar la interfaz normal
st.markdown("<p class='subheader'>Interactúa con tu asistente de convivencia escolar.</p>", unsafe_allow_html=True)

# Agregar ejemplos de preguntas con estilo profesional usando colores CEFA
st.markdown("""
<div style="margin-bottom: 20px;">
    <p style="font-size: 0.9rem; color: #006D2C; margin-bottom: 1rem; font-style: italic; font-family: 'Segoe UI', Arial, sans-serif;">
        Ejemplos de preguntas que puedes hacerle:
    </p>
    <div class="example-question">
        <span>¿Cuáles son los objetivos principales de la Ley 1620 de 2013?</span>
    </div>
    <div class="example-question">
        <span>¿Cuál es la definición y el propósito principal del Manual de Convivencia?</span>
    </div>
    <div class="example-question">
        <span>¿Qué sanciones implica el agredir a un compañero?</span>
    </div>
    <div class="example-question">
        <span>Carolina pérez golpea a Susana morales, en el salón de clase hoy 13 de mayo de 2025 a las 8:30 am, argumentando que susana Morales la agredió verbalmente, el Profesor Rubén Palacio las separó, ¿puedes elaborar el acta para este incidente?</span>
    </div>
</div>
<div class='cefa-decoration'></div>
""", unsafe_allow_html=True)

# Sidebar para configuración
st.sidebar.markdown("<h2 style='color: #006D2C;'>Configuración</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='cefa-decoration'></div>", unsafe_allow_html=True)

# Mostrar información de conexión actual
st.sidebar.success("✅ Configuración cargada")
with st.sidebar.expander("Ver configuración actual"):
    st.code(f"Endpoint: {st.session_state.agent_endpoint}\nClave de acceso: {'*'*10}")

# Ajustes avanzados
with st.sidebar.expander("Ajustes avanzados"):
    temperature = st.slider("Temperatura", min_value=0.0, max_value=1.0, value=0.2, step=0.1,
                          help="Valores más altos generan respuestas más creativas, valores más bajos generan respuestas más deterministas.")
    
    max_tokens = st.slider("Longitud máxima", min_value=100, max_value=2000, value=1000, step=100,
                          help="Número máximo de tokens en la respuesta.")

# Sección para probar conexión con el agente
with st.sidebar.expander("Probar conexión"):
    if st.button("Verificar endpoint"):
        with st.spinner("Verificando conexión..."):
            try:
                agent_endpoint = st.session_state.agent_endpoint
                agent_access_key = st.session_state.agent_access_key
                
                if not agent_endpoint or not agent_access_key:
                    st.error("Falta configuración del endpoint o clave de acceso")
                else:
                    # Asegurarse de que el endpoint termine correctamente
                    if not agent_endpoint.endswith("/"):
                        agent_endpoint += "/"
                    
                    # Verificar si la documentación está disponible (común en estos endpoints)
                    docs_url = f"{agent_endpoint}docs"
                    
                    # Preparar headers
                    headers = {
                        "Authorization": f"Bearer {agent_access_key}",
                        "Content-Type": "application/json"
                    }
                    
                    try:
                        # Primero intentar verificar si hay documentación disponible
                        response = requests.get(docs_url, timeout=10)
                        
                        if response.status_code < 400:
                            st.success(f"✅ Documentación del agente accesible en: {docs_url}")
                        
                        # Luego intentar hacer una solicitud simple para verificar la conexión
                        completions_url = f"{agent_endpoint}api/v1/chat/completions"
                        test_payload = {
                            "model": "n/a",
                            "messages": [{"role": "user", "content": "Hello"}],
                            "max_tokens": 5,
                            "stream": False
                        }
                        
                        response = requests.post(completions_url, headers=headers, json=test_payload, timeout=10)
                        
                        if response.status_code < 400:
                            st.success(f"✅ Conexión exitosa con el endpoint del agente")
                            with st.expander("Ver detalles de la respuesta"):
                                try:
                                    st.json(response.json())
                                except:
                                    st.code(response.text)
                            st.info("🔍 La API está configurada correctamente y responde a las solicitudes.")
                        else:
                            st.error(f"❌ Error al conectar con el agente. Código: {response.status_code}")
                            with st.expander("Ver detalles del error"):
                                st.code(response.text)
                    except Exception as e:
                        st.error(f"Error de conexión: {str(e)}")
            except Exception as e:
                st.error(f"Error al verificar endpoint: {str(e)}")

# Opciones de gestión de conversación
st.sidebar.markdown("<h3 style='color: #008F39;'>Gestión de conversación</h3>", unsafe_allow_html=True)
st.sidebar.markdown("<div class='cefa-decoration'></div>", unsafe_allow_html=True)

# Botón para limpiar conversación
if st.sidebar.button("🗑️ Limpiar conversación"):
    st.session_state.messages = []
    st.rerun()

# Botón para guardar conversación en PDF
if st.sidebar.button("💾 Guardar conversación en PDF"):
    # Crear PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Configurar colores CEFA en el PDF
    # Verde CEFA aproximado en RGB
    pdf.set_draw_color(0, 143, 57)  # Verde CEFA
    pdf.set_fill_color(255, 215, 0)  # Amarillo CEFA
    
    # Añadir título con colores CEFA
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 109, 44)  # Verde CEFA oscuro
    pdf.cell(200, 10, "Conversación con el Asistente CEFA", ln=True, align='C')
    
    # Línea decorativa con colores CEFA
    pdf.line(10, 25, 200, 25)
    pdf.ln(15)
    
    # Añadir fecha
    from datetime import datetime
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(102, 102, 102)  # Gris
    pdf.cell(200, 10, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
    pdf.ln(10)
    
    # Recuperar mensajes
    pdf.set_font("Arial", size=12)
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            pdf.set_text_color(0, 109, 44)  # Verde CEFA oscuro
            pdf.cell(200, 10, "Usuario:", ln=True)
        else:
            pdf.set_text_color(184, 134, 11)  # Amarillo dorado oscuro
            pdf.cell(200, 10, "Asistente:", ln=True)
        
        pdf.set_text_color(0, 0, 0)  # Negro para el contenido
        
        # Partir el texto en múltiples líneas si es necesario
        text = msg["content"]
        pdf.multi_cell(190, 10, text)
        pdf.ln(5)
    
    # Guardar el PDF en un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        pdf_path = tmp_file.name
        pdf.output(pdf_path)
    
    # Abrir y leer el archivo para la descarga
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    
    # Botón de descarga
    st.sidebar.download_button(
        label="Descargar PDF",
        data=pdf_data,
        file_name="conversacion_convivencia_cefa.pdf",
        mime="application/pdf",
    )

# Botón para cerrar sesión
if st.sidebar.button("Cerrar sesión"):
    st.session_state.is_configured = False
    st.session_state.agent_access_key = ""
    st.rerun()

# Función para verificar si hay URLs de imagen en la respuesta
def extract_and_process_images(text):
    import re
    # Patrón específico para URLs de gráficos de tu sistema
    chart_pattern = r'https?://[^\s\)\]\}]+/chart\?[^\s\)\]\}]+'
    
    # Patrones adicionales para otros tipos de imágenes
    image_patterns = [
        chart_pattern,  # URLs de gráficos de tu sistema
        r'https?://[^\s\)\]\}]+\.(?:jpg|jpeg|png|gif|webp|svg)',
        r'https?://[^\s\)\]\}]+\.(?:JPG|JPEG|PNG|GIF|WEBP|SVG)',
        r'data:image/[^;]+;base64,[^\s]+'
    ]
    
    images_found = []
    for pattern in image_patterns:
        images_found.extend(re.findall(pattern, text))
    
    # Eliminar duplicados manteniendo el orden
    images_found = list(dict.fromkeys(images_found))
    
    # Simplificar el texto removiendo las URLs de imágenes
    simplified_text = text
    for img_url in images_found:
        simplified_text = simplified_text.replace(img_url, ' ')
    
    return simplified_text, images_found

# Función para enviar consulta al agente
def query_agent(prompt, history=None):
    try:
        # Obtener configuración del agente
        agent_endpoint = st.session_state.agent_endpoint
        agent_access_key = st.session_state.agent_access_key
        
        if not agent_endpoint or not agent_access_key:
            return {"error": "Las credenciales de API no están configuradas correctamente."}
        
        # Asegurarse de que el endpoint termine correctamente
        if not agent_endpoint.endswith("/"):
            agent_endpoint += "/"
        
        # Construir URL para chat completions
        completions_url = f"{agent_endpoint}api/v1/chat/completions"
        
        # Preparar headers con autenticación
        headers = {
            "Authorization": f"Bearer {agent_access_key}",
            "Content-Type": "application/json"
        }
        
        # Preparar los mensajes en formato OpenAI
        messages = []
        if history:
            messages.extend([{"role": msg["role"], "content": msg["content"]} for msg in history])
        messages.append({"role": "user", "content": prompt})
        
        # Construir el payload
        payload = {
            "model": "n/a",  # El modelo no es relevante para el agente
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        # Enviar solicitud POST
        try:
            response = requests.post(completions_url, headers=headers, json=payload, timeout=60)
            
            # Verificar respuesta
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Procesar la respuesta en formato OpenAI
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        choice = response_data["choices"][0]
                        if "message" in choice and "content" in choice["message"]:
                            result = {
                                "response": choice["message"]["content"]
                            }
                            return result
                    
                    # Si no se encuentra la estructura esperada
                    return {"error": "Formato de respuesta inesperado", "details": str(response_data)}
                except ValueError:
                    # Si no es JSON, devolver el texto plano
                    return {"response": response.text}
            else:
                # Error en la respuesta
                error_message = f"Error en la solicitud. Código: {response.status_code}"
                try:
                    error_details = response.json()
                    return {"error": error_message, "details": str(error_details)}
                except:
                    return {"error": error_message, "details": response.text}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"Error en la solicitud HTTP: {str(e)}"}
        
    except Exception as e:
        return {"error": f"Error al comunicarse con el asistente: {str(e)}"}

# Crear un contenedor para el historial de chat con un estilo mejorado
chat_container = st.container()
with chat_container:
    # Mostrar historial de conversación
    for message in st.session_state.messages:
        # Aplicar estilos diferentes según el rol
        role_style = "user" if message["role"] == "user" else "assistant"
        
        with st.chat_message(message["role"]):
            # Procesar mensajes del historial para extrair imágenes
            if message["role"] == "assistant":
                content = message["content"]
                simplified_text, image_urls = extract_and_process_images(content)
                st.markdown(simplified_text)
                
                # Mostrar las imágenes encontradas
                if image_urls:
                    for idx, img_url in enumerate(image_urls):
                        # Crear un enlace estilizado con colores CEFA
                        st.markdown(f"""
                        <a href="{img_url}" target="_blank" style="display: inline-block; margin: 5px 0; padding: 8px 12px; background-color: rgba(255, 215, 0, 0.1); color: #006D2C; border-radius: 4px; text-decoration: none; font-size: 14px; border: 1px solid #008F39;">
                            <span style="display: flex; align-items: center;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#008F39" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                                    <polyline points="21 15 16 10 5 21"></polyline>
                                </svg>
                                Ver gráfico en nueva pestaña
                            </span>
                        </a>
                        """, unsafe_allow_html=True)
            else:
                st.markdown(message["content"])
            
            # Si es un mensaje del asistente y tiene audio asociado, mostrarlo
            if message["role"] == "assistant" and "audio_html" in message:
                st.markdown(message["audio_html"], unsafe_allow_html=True)

# Campo de entrada para el mensaje con estilo mejorado
prompt = st.chat_input("Escribe tu pregunta aquí...")

# Procesar la entrada del usuario
if prompt:
    # Añadir mensaje del usuario al historial
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Mostrar mensaje del usuario
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Preparar historial para la API
    api_history = st.session_state.messages[:-1]  # Excluir el mensaje actual
    
    # Mostrar indicador de carga mientras se procesa
    with st.chat_message("assistant"):
        with st.spinner("Analizando tu consulta..."):
            # Enviar consulta al agente
            response = query_agent(prompt, api_history)
            
            if "error" in response:
                st.error(f"Error: {response['error']}")
                if "details" in response:
                    with st.expander("Detalles del error"):
                        st.code(response["details"])
                
                # Añadir mensaje de error al historial
                error_msg = f"Lo siento, ocurrió un error al procesar tu solicitud: {response['error']}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            else:
                # Mostrar respuesta del asistente
                response_text = response.get("response", "No se recibió respuesta del agente.")
                
                # Procesar la respuesta para extrair imágenes
                simplified_text, image_urls = extract_and_process_images(response_text)
                
                # Mostrar el texto simplificado
                st.markdown(simplified_text)
                
                # Mostrar las imágenes encontradas
                if image_urls:
                    for idx, img_url in enumerate(image_urls):
                        # Crear un enlace estilizado con colores CEFA
                        st.markdown(f"""
                        <a href="{img_url}" target="_blank" style="display: inline-block; margin: 5px 0; padding: 8px 12px; background-color: rgba(255, 215, 0, 0.1); color: #006D2C; border-radius: 4px; text-decoration: none; font-size: 14px; border: 1px solid #008F39;">
                            <span style="display: flex; align-items: center;">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#008F39" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;">
                                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                                    <polyline points="21 15 16 10 5 21"></polyline>
                                </svg>
                                Ver gráfico en nueva pestaña
                            </span>
                        </a>
                        """, unsafe_allow_html=True)
                
                # Generar audio (siempre)
                audio_html = None
                with st.spinner("Generando audio..."):
                    audio_html = text_to_speech(simplified_text)
                    st.markdown(audio_html, unsafe_allow_html=True)
                
                # Añadir respuesta al historial con el audio
                message_data = {"role": "assistant", "content": response_text}
                if audio_html:
                    message_data["audio_html"] = audio_html
                st.session_state.messages.append(message_data)

# Pie de página con estilo mejorado usando colores CEFA
st.markdown("""
<div class='footer'>
    <div style="display: flex; justify-content: center; align-items: center; gap: 10px;">
        <span style="color: #006D2C; font-weight: 500;">Asistente Digital CEFA © 2025</span>
        <span style="color: #FFD700; font-size: 18px;">•</span>
        <span style="color: #333333;">Centro Formativo de Antioquia</span>
    </div>
</div>
""", unsafe_allow_html=True)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import yt_dlp
import logging
from mega import Mega
import requests  # Importando o requests
from tenacity import retry, wait_exponential

# Configurando o logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

@retry(wait=wait_exponential(multiplier=1, min=4, max=10))
def upload_to_mega(file_path):
    mega = Mega()
    m = mega.login()  # Login anônimo
    mega_file = m.upload(file_path)  # Faz o upload
    return mega.get_link(mega_file)  # Retorna o link

async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Instruções para encontrar links", callback_data='instructions')],
        [InlineKeyboardButton("Limites e Formatos", callback_data='limits')],
        [InlineKeyboardButton("Baixar Vídeo", callback_data='download_video')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Bem-vindo! Escolha uma opção:', reply_markup=reply_markup)

async def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'instructions':
        instructions = (
            "Instruções para encontrar links de vídeos:\n"
            "1. Abra a página do vídeo desejado.\n"
            "2. Clique com o botão direito e selecione 'Inspecionar' ou pressione F12.\n"
            "3. No painel, pressione Ctrl + F para buscar.\n"
            "4. Pesquise por palavras-chave como:\n"
            "   - video\n"
            "   - iframe\n"
            "   - embed\n"
            "5. Copie o link encontrado nos atributos src ou data."
        )
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(instructions, reply_markup=reply_markup)

    elif query.data == 'limits':
        limits_info = (
            "Limites e Formatos:\n"
            "- Tamanho máximo do vídeo: 250 MB\n"
            "- Formatos suportados: MP4, MKV, etc."
        )
        keyboard = [[InlineKeyboardButton("Voltar", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(limits_info, reply_markup=reply_markup)

    elif query.data == 'download_video':
        await query.edit_message_text("Envie o link do vídeo que deseja baixar.")

    elif query.data == 'back':
        await start(query.message, context)

async def download_video(update: Update, context: CallbackContext) -> None:
    link = update.message.text
    await update.message.reply_text('Baixando o vídeo...')

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'max_filesize': 250 * 1024 * 1024,
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            video_file = ydl.prepare_filename(info_dict)

        # Fazer upload para o MEGA
        mega_link = upload_to_mega(video_file)
        await update.message.reply_text(f'Vídeo enviado com sucesso! Acesse aqui: {mega_link}')

    except Exception as e:
        logging.error(f"Erro ao baixar o vídeo: {str(e)}")
        await update.message.reply_text(f'Ocorreu um erro: {str(e)}')

def main() -> None:
    token = "7463903034:AAGPu_qcrUdZ5jYvJbZFLjTR4qJOyJVpaDg"  # Substitua pelo seu token
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    app.add_handler(CallbackQueryHandler(button_callback))

    app.run_polling()

if __name__ == '__main__':
    main()

import telebot
import requests

API_TOKEN = '7974801115:AAHfUy4EQ0AH076yh93mig1yodRCHKv2Vug'
API_KEY = 'eyJhcHAiOiIxMTQ3NDAiLCJhdXRoIjoiMjAyMjA5MjkiLCJzaWduIjoiV2E2ZnBEWG9od3dYcE95T1ZQWFZiZz09In0='
API_BASE_URL = 'https://openapi.bukaolshop.net/v1'
ADMIN_ID = 5184838917

bot = telebot.TeleBot(API_TOKEN)
user_states = {}
headers = { 'Authorization': f'Bearer {API_KEY}' }

@bot.message_handler(commands=['ubahsaldo'])
def ubah_saldo_start(message):
    if message.chat.id != ADMIN_ID:
        return
    try:
        response = requests.get(f"{API_BASE_URL}/member/list?page=1", headers=headers)
        result = response.json()
        if result.get('code') != 200 or 'data' not in result:
            bot.send_message(message.chat.id, "❌ Gagal mengambil daftar member.")
            return
        members = result['data'][:5]
        for m in members:
            text = f"👤 *{m['nama_user']}*\n📧 {m['email_user']}\n📱 {m['nomor_telepon']}"
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.add(telebot.types.InlineKeyboardButton("Ubah Saldo", callback_data=f"ubahsaldo_{m['id_user']}"))
            bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error:
{str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("ubahsaldo_"))
def pilih_user_ubah_saldo(call):
    id_user = call.data.split("_")[1]
    user_states[call.message.chat.id] = {'id_user': id_user, 'step': 'minta_tipe'}
    bot.answer_callback_query(call.id, "User dipilih.")
    bot.send_message(call.message.chat.id, "Masukkan tipe saldo: *tambah* atau *kurang*", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.chat.id in user_states and user_states[m.chat.id]['step'] == 'minta_tipe')
def handle_tipe_saldo(message):
    tipe = message.text.lower().strip()
    if tipe not in ['tambah', 'kurang']:
        bot.send_message(message.chat.id, "❗ Harus *tambah* atau *kurang*", parse_mode="Markdown")
        return
    user_states[message.chat.id]['tipe'] = tipe
    user_states[message.chat.id]['step'] = 'minta_jumlah'
    bot.send_message(message.chat.id, "Masukkan jumlah saldo (angka):")

@bot.message_handler(func=lambda m: m.chat.id in user_states and user_states[m.chat.id]['step'] == 'minta_jumlah')
def handle_jumlah_saldo(message):
    try:
        jumlah = int(message.text)
        if jumlah <= 0:
            raise ValueError()
    except:
        bot.send_message(message.chat.id, "❗ Jumlah harus angka positif.")
        return
    state = user_states[message.chat.id]
    payload = { 'id_user': state['id_user'], 'tipe': state['tipe'], 'jumlah': jumlah }
    try:
        res = requests.post(f"{API_BASE_URL}/member/saldo", data=payload, headers=headers)
        result = res.json()
        if result.get('code') == 200:
            bot.send_message(message.chat.id, f"✅ Saldo berhasil diubah.\nTipe: {state['tipe']}\nJumlah: Rp{jumlah}")
        else:
            bot.send_message(message.chat.id, f"❌ Gagal: {result.get('status')}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")
    user_states.pop(message.chat.id)

@bot.message_handler(commands=['konfirmasitopup'])
def konfirmasi_topup(message):
    if message.chat.id != ADMIN_ID:
        return
    user_states[message.chat.id] = {'step': 'token_topup'}
    bot.send_message(message.chat.id, "Masukkan *token_topup* dari halaman topup:", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.chat.id in user_states and user_states[m.chat.id]['step'] == 'token_topup')
def handle_token_topup(message):
    token = message.text.strip()
    try:
        response = requests.post(f"{API_BASE_URL}/member/topup", data={'token_topup': token}, headers=headers)
        result = response.json()
        if result.get('code') == 200:
            bot.send_message(message.chat.id, f"✅ Topup berhasil!\n👤 {result['nama_user']}\n📧 {result['email_user']}\n💰 Rp{result['jumlah']}")
        else:
            bot.send_message(message.chat.id, f"❌ Gagal: {result.get('status')}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error:
{str(e)}")
    user_states.pop(message.chat.id)

bot.polling()

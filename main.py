import sys
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
import re
from datetime import datetime
import os

# Configurações fixas
api_id = 24687094
api_hash = "5e2b082fd267728c84965b60b6787468"
phone = "+5592993446488"
bot_username = "@puxadasSeven"

# Inicializa o cliente Telegram
client = TelegramClient("session_name", api_id, api_hash)

# Modelo de entrada para o CPF
class CPFInput(BaseModel):
    cpf: str

# Inicializa o app FastAPI
app = FastAPI()

# Função para normalizar e validar CPF
def validate_cpf(cpf: str) -> str:
    cpf = re.sub(r'[.\-\s]', '', cpf)
    if not (cpf.isdigit() and len(cpf) == 11):
        raise HTTPException(status_code=400, detail="CPF inválido. Deve conter exatamente 11 dígitos.")
    return cpf

# Função de parsing da resposta (mesma do código original)
def parse_response(response, expected_cpf):
    if not response or "CPF NÃO ENCONTRADO" in response.upper():
        return {
            "Erro": "Nenhuma resposta recebida" if not response else "CPF NÃO ENCONTRADO",
            "CPF": expected_cpf,
            "Data_Hora": "",
            **{field: "SEM INFORMAÇÃO" for field in [
                "PIS", "Título Eleitoral", "RG", "Data Expedição", "Orgão Expedidor", "UF RG",
                "Nome", "Nascimento", "Idade", "Signo", "Mãe", "Pai", "Nacionalidade",
                "Escolaridade", "Estado Civil", "Profissão", "Renda Presumida", "Status Receita",
                "Score", "Faixa de Risco", "E-mails", "Endereço", "Telefones Proprietário",
                "Telefones Comerciais", "Telefones Referenciais", "Possíveis Parentes",
                "Possíveis Vizinhos", "Participação Societária", "Vínculos Empregatícios"
            ]}
        }

    response = re.sub(r"\*\*|\`", "", response)
    response = re.sub(r"[🔍🔛].*?\n|BY: @SkynetBlackRobot|USUÁRIO:.*?(?=\n|$)", "", response, flags=re.IGNORECASE)
    response = re.sub(r"\n\s*\n", "\n", response).strip()

    lines = [re.sub(r"^\s*•\s*", "", line.strip()) for line in response.splitlines() if line.strip() and not re.match(r"^[🔍🔛]*$", line.strip())]

    fields = [
        "CPF", "Data_Hora", "PIS", "Título Eleitoral", "RG", "Data Expedição", "Orgão Expedidor",
        "UF RG", "Nome", "Nascimento", "Idade", "Signo", "Mãe", "Pai", "Nacionalidade",
        "Escolaridade", "Estado Civil", "Profissão", "Renda Presumida", "Status Receita",
        "Score", "Faixa de Risco", "E-mails", "Endereço", "Telefones Proprietário",
        "Telefones Comerciais", "Telefones Referenciais", "Possíveis Parentes",
        "Possíveis Vizinhos", "Participação Societária", "Vínculos Empregatícios"
    ]

    result = {field: [] if field in ["E-mails", "Endereço", "Telefones Proprietário", "Participação Societária", "Possíveis Parentes", "Vínculos Empregatícios"] else "SEM INFORMAÇÃO" for field in fields}
    result["CPF"] = expected_cpf
    result["Erro"] = ""

    label_map = {
        "CPF": "CPF",
        "PIS": "PIS",
        "TÍTULO ELEITORAL": "Título Eleitoral",
        "RG": "RG",
        "DATA DE EXPEDIÇÃO": "Data Expedição",
        "ORGÃO EXPEDIDOR": "Orgão Expedidor",
        "UF - RG": "UF RG",
        "NOME": "Nome",
        "NASCIMENTO": "Nascimento",
        "IDADE": "Idade",
        "SIGNO": "Signo",
        "MÃE": "Mãe",
        "PAI": "Pai",
        "NACIONALIDADE": "Nacionalidade",
        "ESCOLARIDADE": "Escolaridade",
        "ESTADO CIVIL": "Estado Civil",
        "PROFISSÃO": "Profissão",
        "RENDA PRESUMIDA": "Renda Presumida",
        "STATUS RECEITA FEDERAL": "Status Receita",
        "SCORE": "Score",
        "FAIXA DE RISCO": "Faixa de Risco",
        "E-MAILS": "E-mails",
        "ENDEREÇOS": "Endereço",
        "TELEFONES PROPRIETÁRIO": "Telefones Proprietário",
        "TELEFONES COMERCIAIS": "Telefones Comerciais",
        "TELEFONES REFERENCIAIS": "Telefones Referenciais",
        "POSSÍVEIS PARENTES": "Possíveis Parentes",
        "POSSÍVEIS VIZINHOS": "Possíveis Vizinhos",
        "PARTICIPAÇÃO SOCIETÁRIA": "Participação Societária",
        "VÍNCULOS EMPREGATÍCIOS": "Vínculos Empregatícios"
    }

    current_field = None
    for line in lines:
        if ":" in line and not (current_field in ["Participação Societária", "Possíveis Parentes", "Vínculos Empregatícios"] and line.strip().startswith(("CNPJ:", "CARGO:", "NOME:", "CPF:", "PARENTESCO:", "ADMISSÃO:"))):
            label, value = map(str.strip, line.split(":", 1))
            label = label.upper()
            if label in label_map:
                current_field = label_map[label]
                if current_field in ["E-mails", "Endereço", "Telefones Proprietário", "Participação Societária", "Possíveis Parentes", "Vínculos Empregatícios"]:
                    result[current_field] = [value] if value and value != "SEM INFORMAÇÃO" else []
                else:
                    result[current_field] = value if value else "SEM INFORMAÇÃO"
            else:
                current_field = None
        elif current_field and line and not line.startswith(("•", "**•")):
            if current_field in ["E-mails", "Endereço", "Telefones Proprietário", "Participação Societária", "Possíveis Parentes", "Vínculos Empregatícios"]:
                result[current_field].append(line.strip())

    return result

# Função para clicar no botão "Apagar"
async def click_delete_button(client, message):
    if not message.reply_markup:
        return False

    for row in message.reply_markup.rows:
        for button in row.buttons:
            if "apagar" in button.text.lower():
                for attempt in range(5):
                    try:
                        await client(GetBotCallbackAnswerRequest(
                            peer=await client.get_entity(bot_username),
                            msg_id=message.id,
                            data=button.data
                        ))
                        print(f"Botão 'Apagar' clicado na tentativa {attempt + 1}.")
                        return True
                    except Exception as e:
                        print(f"Tentativa {attempt + 1} falhou: {e}")
                        await asyncio.sleep(2)
                return False
    return False

# Endpoint para consultar CPF
@app.post("/consultar-cpf")
async def consultar_cpf(input: CPFInput):
    cpf = validate_cpf(input.cpf)

    try:
        # Inicia o cliente Telegram
        await client.start(phone=phone)
        print("Conectado ao Telegram.")

        # Envia a mensagem ao bot
        sent_message = await client.send_message(bot_username, f"/cpf3 {cpf}")
        print(f"Mensagem enviada. ID: {sent_message.id}")
        await asyncio.sleep(5)

        # Busca a resposta do bot
        async for message in client.iter_messages(bot_username, limit=20, wait_time=150):
            if message and message.id > sent_message.id:
                message_text = message.text or ""
                print(f"Depuração: Mensagem recebida (ID: {message.id}):\n{message_text[:200]}...")

                # Normaliza a mensagem para verificar o CPF
                normalized_message = re.sub(r'[.\-\s]', '', message_text)
                if cpf not in normalized_message and "CPF NÃO ENCONTRADO" not in message_text.upper():
                    print(f"Depuração: Mensagem ignorada, CPF {cpf} não encontrado.")
                    continue

                # Verifica o CPF extraído
                normalized_text = re.sub(r"\*\*|\`", "", message_text)
                extracted_cpf_match = re.search(r"•\s*CPF:\s*([\d.\-]+)", normalized_text, re.MULTILINE)
                if extracted_cpf_match:
                    extracted_cpf = re.sub(r'[.\-\s]', '', extracted_cpf_match.group(1))
                    print(f"Depuração: CPF extraído: {extracted_cpf}")
                    if extracted_cpf != cpf:
                        raise HTTPException(status_code=400, detail=f"CPF extraído ({extracted_cpf}) não corresponde ao inserido ({cpf}).")

                # Faz o parsing da resposta
                parsed_data = parse_response(message_text, cpf)
                parsed_data["Data_Hora"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

                # Tenta clicar no botão "Apagar"
                await asyncio.sleep(5)
                if not await click_delete_button(client, message):
                    print(f"Falha ao clicar no botão 'Apagar' para CPF {cpf}.")

                # Retorna todos os campos no formato JSON
                response = {
                    "cpf": parsed_data["CPF"],
                    "data_hora": parsed_data["Data_Hora"],
                    "pis": parsed_data["PIS"],
                    "titulo_eleitoral": parsed_data["Título Eleitoral"],
                    "rg": parsed_data["RG"],
                    "data_expedicao": parsed_data["Data Expedição"],
                    "orgao_expedidor": parsed_data["Orgão Expedidor"],
                    "uf_rg": parsed_data["UF RG"],
                    "nome": parsed_data["Nome"],
                    "nascimento": parsed_data["Nascimento"],
                    "idade": parsed_data["Idade"],
                    "signo": parsed_data["Signo"],
                    "mae": parsed_data["Mãe"],
                    "pai": parsed_data["Pai"],
                    "nacionalidade": parsed_data["Nacionalidade"],
                    "escolaridade": parsed_data["Escolaridade"],
                    "estado_civil": parsed_data["Estado Civil"],
                    "profissao": parsed_data["Profissão"],
                    "renda_presumida": parsed_data["Renda Presumida"],
                    "status_receita": parsed_data["Status Receita"],
                    "score": parsed_data["Score"],
                    "faixa_de_risco": parsed_data["Faixa de Risco"],
                    "e_mails": parsed_data["E-mails"],
                    "endereco": parsed_data["Endereço"],
                    "telefones_proprietario": parsed_data["Telefones Proprietário"],
                    "telefones_comerciais": parsed_data["Telefones Comerciais"],
                    "telefones_referenciais": parsed_data["Telefones Referenciais"],
                    "possiveis_parentes": parsed_data["Possíveis Parentes"],
                    "possiveis_vizinhos": parsed_data["Possíveis Vizinhos"],
                    "participacao_societaria": parsed_data["Participação Societária"],
                    "vinculos_empregaticios": parsed_data["Vínculos Empregatícios"],
                    "erro": parsed_data["Erro"] if parsed_data["Erro"] else None
                }

                return response

        # Caso não encontre resposta válida
        raise HTTPException(status_code=404, detail="Nenhuma resposta válida recebida do bot.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar CPF {cpf}: {str(e)}")
    finally:
        await client.disconnect()

# Inicia o servidor (executado automaticamente ao rodar o script)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
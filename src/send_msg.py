from tempfile import template
from src.get_data import open_matches, open_mock, open_professional
from src.utils.path import get_project_root
from abc import ABC, abstractmethod
import os
import boto3
import json


base_path = get_project_root()
os.environ.setdefault("DISPLAY", ":0")

class SendMsg(ABC):
    @abstractmethod
    def send_msg(self, fields)-> None:
        pass

    @abstractmethod
    def send_batch(self, df)-> None:
        pass


class AWS_Sender(SendMsg):
    def send_msg(self, fields)-> None:
        client = boto3.client('sesv2', region_name='us-east-2')

        template_data = {
            "name_professional": str(fields["name_professional"]),
            "area": str(fields["area"]),
            "name_paciente": str(fields["name_paciente"]),
            "phone_paciente": str(fields["phone_paciente"]),
        }
        template_json = json.dumps(template_data)

        response = client.send_email(
            FromEmailAddress='no-reply@orgmetamorfosepro.com.br',
            Destination={
                'ToAddresses': [fields["email_professional"]],
            },
            Content={
                'Template': {
                    'TemplateName': 'metamorfose_template',
                    'TemplateData': template_json
                }
            }
        )

        return response

    def send_batch(self,df)-> None:
        df = df.reset_index(drop=True)
        for  index, row in df.iterrows():
            self.send_msg(row)
            print(f"{index + 1} de {len(df)} mensagens enviadas")
        print("Sent all messages")

def create_template(name):
    client = boto3.client('sesv2')
    response = client.create_email_template(
        TemplateName=name,
        TemplateContent={
            'Subject': 'Novos Pacientes!',
            'Text': '''Olá {{name_professional}}, tudo bem? Sou a Inteligência Artificial da Rede MetAMORfose, você assinou conosco como profissional da área de {{area}}.
                Promovemos suas conexões com pacientes - temos Pacientes que sugerem R$150 a R$35 a consulta (para Profissionais Premium) e Pacientes de +R$300 a R$50 por consulta (para Profissionais Platinum e Superior).
                
                Temos um guia de como conversar com paciente em orgmetamorfose.com.br/manual-de-uso 

                Entre em contato com este, que cadastrou buscar atendimento e consentiu ser conectado com você!

                👤Nome: {{name_paciente}}
                📞Contato: wa.me/{{phone_paciente}}
                💰Vocês definem o valor. Recomendamos que o paciente pague, direto para você, antes da teleconsulta!

        
                Não responda esse email. Caso precise de suporte: orgmetamorfose.com.br/suporte
                Obrigada por fazer parte da nossa Rede!.''',
            'Html': '''
                <html>
                <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                    <h2 style="color:#2c3e50;">Olá {{name_professional}}, tudo bem?</h2>
                    <p style="color:#333; text-decoration:none;">
                        Sou a <strong>Inteligência Artificial da Rede MetAMORfose</strong>.  
                        Você se cadastrou conosco como profissional da área de <strong>{{area}}</strong>.<br>
                        Promovemos suas conexões com pacientes - temos Pacientes que sugerem R$150 a R$35 a consulta (para Profissionais Premium) e Pacientes de +R$300 a R$50 por consulta (para Profissionais Platinum e Superior).
                    </p>

                    <p style="color:#333; text-decoration:none;">
                        📘 Consulte nosso guia de comunicação:<a href="https://orgmetamorfose.com.br/manual-de-uso" target="_blank">orgmetamorfose.com.br/manual-de-uso</a>
                    </p>
                    <p style="color:#333; text-decoration:none;">
                        🛠️ Caso precise de suporte:<a href="https://orgmetamorfose.com.br/suporte" target="_blank">orgmetamorfose.com.br/suporte</a>  
                    </p>
                    

                    <hr style="border: 1px solid #ddd; color:#333;margin 20px 0;">
                    <h3 style="color:#333; text-decoration:none;">📩 Novo paciente interessado:</h3>
                    <ul style="color:#333; list-style:none; padding:0; margin:0;">
                        <li>
                            <strong style="color:#333;">👤 Nome:</strong> {{name_paciente}}
                        </li>
                        <li>
                            <strong style="color:#333;">💰 Pagamento:</strong> <span style="color:#333;"> Vocês definem o valor. Sugerimos pagamento antes da teleconsulta!</span>
                        </li>
                        <li>
                            <strong style="color:#333;">📞 Contato:</strong> 
                            <a style="color:#333 !important;" href="https://wa.me/{{phone_paciente}}" target="_blank" >
                                wa.me/{{phone_paciente}}
                            </a>
                        </li>
                    </ul>
                    <hr style="border: 1px solid #ddd; color:#333;margin 20px 0;">

                    <span style="color:#888; font-size:12px; margin-bottom:20px;"> Obrigada por fazer parte da nossa Rede!</span>
                    <br>
                    <span style="color:#888; font-size:12px; margin-bottom:20px;"> Equipe MetAMORfose</span>
                    <br>
                    <span style="color:#888; font-size:12px; margin-bottom:20px;"> Por favor, não responda esse email.</span>
                </body>
                </html>
            '''
        }
    )

    print("Template criado")
    return response

def delete_template(name):
    client = boto3.client('sesv2')
    response = client.delete_email_template(
        TemplateName=name
    )
    print("Template deletado!")

def check_templates(name):
    client = boto3.client('sesv2')
    response = client.list_email_templates(
        PageSize=10,
        NextToken=''
    )
    templates = [template['TemplateName'] for template in response['TemplatesMetadata']]
    if name in templates:
        print(f"Template {name} já existe.")
        return True
    else:
        print(f"Template {name} não existe.")
        return False

if __name__ == '__main__':
    template_name = 'metamorfose_template'
    # check = check_templates(template_name)
    # if check:
    #     delete_template(template_name)
    # create_template(template_name)
    df = open_mock()
    sender = AWS_Sender()
    response = sender.send_batch(df)
    print(response)

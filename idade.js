export default function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ mensagem: 'Método não permitido' });
  }

  const data = req.body?.data;
  if (!data) {
    return res.status(400).json({ valid: false, mensagem: 'Data não fornecida' });
  }

  const [dia, mes, ano] = data.split('/');
  if (!dia || !mes || !ano) {
    return res.status(400).json({ valid: false, mensagem: 'Formato inválido' });
  }

  const nascimento = new Date(`${ano}-${mes}-${dia}`);
  const hoje = new Date();

  let idade = hoje.getFullYear() - nascimento.getFullYear();
  const m = hoje.getMonth() - nascimento.getMonth();
  if (m < 0 || (m === 0 && hoje.getDate() < nascimento.getDate())) idade--;

  const valid = idade >= 21;

  return res.status(200).json({
    valid,
    idade,
    mensagem: valid ? 'Maior de 21 anos' : 'Menor de 21 anos'
  });
}

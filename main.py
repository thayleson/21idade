async function main() {
  const loginUrl = "https://api.bancoprata.com.br/v1/users/login";
  const loginHeaders = {
    "Content-Type": "application/json",
    "Accept": "application/json"
  };
  const loginData = {
    email: "{{contact.email}}",
    password: "{{contact.password}}"
  };

  try {
    // Login request
    const loginResponse = await fetch(loginUrl, {
      method: "POST",
      headers: loginHeaders,
      body: JSON.stringify(loginData)
    });
    const loginResult = await loginResponse.json();

    if (loginResponse.status !== 200) {
      return { error: `Falha no login: ${loginResponse.status} - ${JSON.stringify(loginResult)}` };
    }

    const token = loginResult?.data?.token;
    if (!token) {
      return { error: "Token não encontrado na resposta" };
    }

    // Balance request
    const balanceUrl = `https://api.bancoprata.com.br/v1/private-payroll/balance?document={{contact.cpf}}&registration_number=`;
    const balanceResponse = await fetch(balanceUrl, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Accept": "application/json"
      }
    });
    const balanceResult = await balanceResponse.json();

    if (balanceResponse.status === 200) {
      return balanceResult;
    } else {
      const errorMessage = balanceResult?.error?.message || "";
      if (errorMessage.includes("Infelizmente não foi possível encontrar este registro")) {
        return { message: "Termo de autorização: Infelizmente não foi possível encontrar este registro." };
      } else {
        // Processar mensagem de erro
        const lines = errorMessage.split("\n").filter(line => line.trim());
        let formattedMessage = "O vínculo empregatício consultado está inelegível\n\nPossíveis motivos:\n";
        for (let i = 2; i < lines.length; i++) {
          if (lines[i].trim()) {
            formattedMessage += `- ${lines[i].trim()}\n`;
          }
        }
        return { message: formattedMessage.trim() };
      }
    }
  } catch (error) {
    return { error: `Erro: ${error.message}` };
  }
}

main();

# Gere com o Python do seu ambiente virtual, sem precisar ativar o ambiente.
param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$pastaProjeto = Split-Path -Parent $PSScriptRoot

function Testar-Executavel([string]$Executavel, [string]$Relatorio) {
    # Um relatorio antigo nunca deve fazer uma nova execucao parecer aprovada.
    if (Test-Path -LiteralPath $Relatorio) { Remove-Item -LiteralPath $Relatorio }
    $caminhoOriginal = $env:PATH
    try {
        # O pacote precisa funcionar sem encontrar Python instalado no PATH.
        $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
        $processo = Start-Process -FilePath $Executavel -ArgumentList @('--verificar-instalacao', ('"' + $Relatorio + '"')) -WindowStyle Hidden -PassThru
        if (-not $processo.WaitForExit(60000)) {
            Stop-Process -Id $processo.Id
            throw 'A verificacao excedeu 60 segundos.'
        }
        $processo.WaitForExit()
        if (Test-Path -LiteralPath $Relatorio) { Get-Content -LiteralPath $Relatorio }
        if ($processo.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $Relatorio)) {
            throw 'O executavel nao passou na verificacao.'
        }
        $resultado = Get-Content -LiteralPath $Relatorio -Raw | ConvertFrom-Json
        if (-not $resultado.sucesso -or -not $resultado.empacotado) {
            throw 'O diagnostico nao confirmou um pacote funcional.'
        }
    } finally {
        $env:PATH = $caminhoOriginal
    }
}

Push-Location -LiteralPath $pastaProjeto
try {
    & $Python -m unittest discover -s testes -v
    if ($LASTEXITCODE -ne 0) { throw 'Os testes falharam.' }

    # Primeiro verifica a coleta de bibliotecas em pasta; depois gera arquivo unico.
    & $Python -m PyInstaller --noconfirm --clean --onedir --windowed --collect-data mancala --name MancalaSoJoga --specpath build iniciar.pyw
    if ($LASTEXITCODE -ne 0) { throw 'O empacotamento em pasta falhou.' }
    Testar-Executavel (Join-Path $pastaProjeto 'dist\MancalaSoJoga\MancalaSoJoga.exe') (Join-Path $pastaProjeto 'build\verificacao-pasta.json')

    & $Python -m PyInstaller --noconfirm --clean --onefile --windowed --collect-data mancala --name MancalaSoJoga --distpath dist/arquivo-unico --workpath build/arquivo-unico --specpath build/arquivo-unico iniciar.pyw
    if ($LASTEXITCODE -ne 0) { throw 'O empacotamento em arquivo unico falhou.' }
    Testar-Executavel (Join-Path $pastaProjeto 'dist\arquivo-unico\MancalaSoJoga.exe') (Join-Path $pastaProjeto 'build\verificacao-arquivo-unico.json')

    $pastaDistribuicao = 'dist\distribuicao\MancalaSoJoga'
    New-Item -ItemType Directory -Force -Path $pastaDistribuicao | Out-Null
    Copy-Item -LiteralPath 'dist\arquivo-unico\MancalaSoJoga.exe', 'COMO-JOGAR.txt' -Destination $pastaDistribuicao
    Compress-Archive -LiteralPath $pastaDistribuicao -DestinationPath 'dist\MancalaSoJoga-Windows-x64.zip' -Force
    $somas = foreach ($arquivo in @('dist\arquivo-unico\MancalaSoJoga.exe', 'dist\MancalaSoJoga-Windows-x64.zip')) {
        $hash = (Get-FileHash -LiteralPath $arquivo -Algorithm SHA256).Hash.ToLowerInvariant()
        $hash + '  ' + [IO.Path]::GetFileName($arquivo)
    }
    Set-Content -LiteralPath 'dist\SHA256.txt' -Value $somas -Encoding ascii
} finally {
    Pop-Location
}

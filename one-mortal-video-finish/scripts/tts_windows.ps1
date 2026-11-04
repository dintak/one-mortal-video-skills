param(
    [Parameter(Mandatory=$true)][string]$Text,
    [Parameter(Mandatory=$true)][string]$Out,
    [string]$Voice
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    if ($Voice) { $speaker.SelectVoice($Voice) }
    $target = [System.IO.Path]::GetFullPath($Out)
    [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($target)) | Out-Null
    $speaker.SetOutputToWaveFile($target)
    $speaker.Speak($Text)
    $speaker.SetOutputToNull()
    Write-Output $target
} finally {
    $speaker.Dispose()
}

$ErrorActionPreference = 'Stop'
$pptx = "C:\Users\MI\Documents\pegawai-ai-backend\local_setup\cs_workflow\COLORBOX_CS_WhatsApp_Day4-5_Validation.pptx"
$outDir = "C:\Users\MI\.openmausbot\task-workspaces\5ccb6477-64f6-40a1-8d2f-9fa4ba5eb8f3\c36ce5b6-ee46-4765-9873-218ffad05481\deck_preview"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }
$app = New-Object -ComObject PowerPoint.Application
$pres = $app.Presentations.Open($pptx, $true, $false, $false)
$i = 1
foreach ($slide in $pres.Slides) {
    $path = Join-Path $outDir ("slide{0}.png" -f $i)
    $slide.Export($path, "PNG", 1600, 900)
    $i++
}
$pres.Close()
$app.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
Get-ChildItem $outDir | Select-Object Name, Length

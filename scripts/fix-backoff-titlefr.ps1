# Remove invalid titleFr entries (BACKOFF marker) from de-*.md
$scriptRoot = if ($MyInvocation.MyCommand.Path) { Split-Path -Parent $MyInvocation.MyCommand.Path } else { (Get-Location).Path }
$siteRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot '..'))
$chapitresDir = Join-Path $siteRoot 'src\content\chapitres'
$n = 0
foreach ($f in (Get-ChildItem -LiteralPath $chapitresDir -Filter 'de-*.md')) {
  $c = [System.IO.File]::ReadAllText($f.FullName, (New-Object System.Text.UTF8Encoding($false)))
  if ($c -match 'titleFr: "BACKOFF') {
    $new = [regex]::Replace($c, '^titleFr: ".*"\r?\n', '', [System.Text.RegularExpressions.RegexOptions]::Multiline)
    [System.IO.File]::WriteAllText($f.FullName, $new, (New-Object System.Text.UTF8Encoding($false)))
    Write-Output "fixed $($f.Name)"
    $n++
  }
}
Write-Output "DONE fixed $n"
# Remove "NNNN - " prefix from title in all de-NNNN.md, keep everything else.
$scriptRoot = if ($MyInvocation.MyCommand.Path) { Split-Path -Parent $MyInvocation.MyCommand.Path } else { (Get-Location).Path }
$siteRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot '..'))
$chapitresDir = Join-Path $siteRoot 'src\content\chapitres'

$n = 0
foreach ($f in (Get-ChildItem -LiteralPath $chapitresDir -Filter 'de-*.md')) {
  $c = [System.IO.File]::ReadAllText($f.FullName, (New-Object System.Text.UTF8Encoding($false)))
  $new = [regex]::Replace($c, '^(title: ")\d{4}\s*-\s*', '$1', [System.Text.RegularExpressions.RegexOptions]::Multiline)
  if ($new -ne $c) {
    [System.IO.File]::WriteAllText($f.FullName, $new, (New-Object System.Text.UTF8Encoding($false)))
    $n++
  }
}
Write-Output "fixed $n files"
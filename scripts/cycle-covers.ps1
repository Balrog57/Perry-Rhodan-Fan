# Download cycle covers from rhodan.stellarque.com and set cover: in cycle frontmatter
$scriptRoot = if ($MyInvocation.MyCommand.Path) { Split-Path -Parent $MyInvocation.MyCommand.Path } else { (Get-Location).Path }
$siteRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot '..'))
$cyclesDir = Join-Path $siteRoot 'src\content\cycles'
$coversDir = Join-Path $siteRoot 'public\images\covers'

$localFr = @{
  1 = 'fr-001.webp'; 2 = 'fr-022.webp'; 3 = 'fr-044.webp'; 4 = 'fr-066.webp'; 5 = 'fr-088.webp'
  6 = 'fr-138.webp'; 7 = 'fr-188.webp'; 8 = 'fr-216.webp'; 9 = 'fr-234.webp'; 11 = 'fr-242.webp'
  12 = 'fr-256.webp'; 13 = 'fr-282.webp'; 14 = 'fr-298.webp'; 15 = 'fr-306.webp'; 16 = 'fr-332.webp'; 17 = 'fr-354.webp'
}
$localDe = @{ 10 = 'de-0600.webp' }

$remoteDe = @{
  18 = 'pr_vo/18/1200.jpg'; 19 = 'pr_vo/19/1300.jpg'; 20 = 'pr_vo/20/1350.jpg'; 21 = 'pr_vo/21/1400.jpg'
  22 = 'pr_vo/22/1500.jpg'; 23 = 'pr_vo/23/1600.jpg'; 24 = 'pr_vo/24/1650.jpg'; 25 = 'pr_vo/25/1700.jpg'
  26 = 'pr_vo/26/1750.jpg'; 27 = 'pr_vo/27/1800.jpg'; 28 = 'pr_vo/28/1876.jpg'; 29 = 'pr_vo/29/1900.jpg'
  30 = 'pr_vo/30/1950.jpg'; 31 = 'pr_vo/31/2000.jpg'; 32 = 'pr_vo/32/2100.jpg'; 33 = 'pr_vo/33/2200.jpg'
  34 = 'pr_vo/34/2300.jpg'; 35 = 'pr_vo/35/2400.jpg'; 36 = 'pr_vo/36/2500.jpg'; 37 = 'pr_vo/37/2600.jpg'
  38 = 'pr_vo/38/2700.jpg'; 39 = 'pr_vo/39/2800.jpg'; 40 = 'pr_vo/40/2875.jpg'; 41 = 'pr_vo/41/2900.jpg'
  42 = 'pr_vo/42/3000.jpg'; 43 = 'pr_vo/43/3100.jpg'; 44 = 'pr_vo/44/3200.jpg'; 45 = 'pr_vo/45/3300.jpg'
}

$ok = 0
foreach ($cycleNum in 1..46) {
  $file = Join-Path $cyclesDir ("cycle-{0:D2}.md" -f $cycleNum)
  if (-not (Test-Path -LiteralPath $file)) { continue }
  $content = [System.IO.File]::ReadAllText($file, (New-Object System.Text.UTF8Encoding($false)))
  # remove existing cover line
  if ($content -match '^cover: ".*"\r?$') {
    $content = [regex]::Replace($content, '^cover: ".*"\r?\n?', '', [System.Text.RegularExpressions.RegexOptions]::Multiline)
  }

  $coverRef = $null
  if ($localFr.ContainsKey($cycleNum)) {
    $coverRef = "/images/covers/$($localFr[$cycleNum])"
  }
  elseif ($localDe.ContainsKey($cycleNum)) {
    $coverRef = "/images/covers/$($localDe[$cycleNum])"
  }
  elseif ($remoteDe.ContainsKey($cycleNum)) {
    $src = $remoteDe[$cycleNum]
    $destName = "cycle-{0:D2}.jpg" -f $cycleNum
    $dest = Join-Path $coversDir $destName
    try {
      $wc = New-Object System.Net.WebClient
      $wc.DownloadFile("http://rhodan.stellarque.com/covers/$src", $dest)
      $wc.Dispose()
      $coverRef = "/images/covers/$destName"
    } catch {
      Write-Output "cycle $cycleNum : DOWNLOAD FAIL"
    }
  }

  if ($coverRef) {
    $esc = $coverRef.Replace('"', '\\"')
    $content = $content -replace '^---\r?\n', "---`ncover: `"$esc`"`n"
    [System.IO.File]::WriteAllText($file, $content, (New-Object System.Text.UTF8Encoding($false)))
    $ok++
    Write-Output "cycle $cycleNum -> $coverRef"
  } else {
    Write-Output "cycle $cycleNum : no cover"
  }
}
Write-Output "DONE $ok cycles"
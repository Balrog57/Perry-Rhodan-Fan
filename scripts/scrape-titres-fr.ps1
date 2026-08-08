# Scrape French titles (heft.php) with retries + polite delays.
$scriptRoot = if ($MyInvocation.MyCommand.Path) { Split-Path -Parent $MyInvocation.MyCommand.Path } else { (Get-Location).Path }
$siteRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot '..'))
$chapitresDir = Join-Path $siteRoot 'src\content\chapitres'

function Decode-Html {
  param([string]$s)
  $s = [System.Net.WebUtility]::HtmlDecode($s)
  $s = [regex]::Replace($s, '\s+', ' ').Trim()
  return $s
}

function Get-TitleFr([int]$num) {
  for ($attempt = 1; $attempt -le 8; $attempt++) {
    $wc = New-Object System.Net.WebClient
    try {
      $bytes = $wc.DownloadData("http://rhodan.stellarque.com/perryrhodan/heft.php?init=$num")
      $wc.Dispose()
      $utf8strict = New-Object System.Text.UTF8Encoding($false, $true)
      try { $html = $utf8strict.GetString($bytes) } catch { $html = [System.Text.Encoding]::GetEncoding(28591).GetString($bytes) }
      $m = [regex]::Match($html, '<td\s+align="left"><i>(.*?)</i></td>', [System.Text.RegularExpressions.RegexOptions]::Singleline)
      if ($m.Success) { return (Decode-Html $m.Groups[1].Value) }
      return $null
    } catch {
      $wc.Dispose()
      Start-Sleep -Seconds ([Math]::Min(3 * $attempt, 45))
    }
  }
  return $null
}

$files = Get-ChildItem -LiteralPath $chapitresDir -Filter 'de-*.md' | Sort-Object Name
Write-Output "found $($files.Count) chapter files"

$ok = 0; $fail = 0
foreach ($f in $files) {
  $content = [System.IO.File]::ReadAllText($f.FullName, (New-Object System.Text.UTF8Encoding($false)))
  if ($content -match 'titleFr: "') { $ok++; continue }   # already done
  $num = [int]$f.BaseName.Substring(3)
  $mTitle = [regex]::Match($content, 'title: "(.+)"')
  $mOrig  = [regex]::Match($content, 'originalTitle: "(.+)"')
  $mCycle = [regex]::Match($content, 'cycleNumber: (\d+)')
  $mNum   = [regex]::Match($content, 'chapterNumber: (\d+)')
  $mType  = [regex]::Match($content, 'type: (\w+)')
  $mCover = [regex]::Match($content, 'cover: "(.+)"')
  $mAuteur = [regex]::Match($content, 'auteur: "(.+)"')
  $mPar   = [regex]::Match($content, 'parution: "(.+)"')

  $deTitle = ''
  if ($mOrig.Success) { $deTitle = $mOrig.Groups[1].Value }
  elseif ($mTitle.Success) { $deTitle = [regex]::Replace($mTitle.Groups[1].Value, '^\d{4}\s*-\s*', '') }

  $fr = Get-TitleFr $num
  if (-not $fr) { $fail++; Write-Output "NOPE $($f.Name)"; continue }
  $escDe = ($deTitle -replace '\\','\\' -replace '"','\"')
  $escFr = ($fr -replace '\\','\\' -replace '"','\"')
  $cycle = $mCycle.Groups[1].Value
  $num2  = $mNum.Groups[1].Value
  $type  = if ($mType.Success) { $mType.Groups[1].Value } else { 'translation' }
  $cover = if ($mCover.Success) { "`ncover: `"$($mCover.Groups[1].Value)`"" } else { '' }
  $auteur = if ($mAuteur.Success) { "`nauteur: `"$($mAuteur.Groups[1].Value)`"" } else { '' }
  $par   = if ($mPar.Success) { "`nparution: `"$($mPar.Groups[1].Value)`"" } else { '' }

  $md = "---`n" +
        "title: `"$escDe`"`n" +
        "titleFr: `"$escFr`"`n" +
        "cycleNumber: $cycle`n" +
        "chapterNumber: $num2`n" +
        "type: $type`n" +
        "originalTitle: `"$escDe`"$cover$auteur$par`n" +
        "---`n`nWIP`n"
  [System.IO.File]::WriteAllText($f.FullName, $md, (New-Object System.Text.UTF8Encoding($false)))
  $ok++
  if ($ok % 100 -eq 0) { Write-Output "progress: $ok" }
  Start-Sleep -Milliseconds 1200
}
Write-Output "DONE ok=$ok fail=$fail"
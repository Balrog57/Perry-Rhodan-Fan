# Extract French translations for PR 600-649 from the French Sammelband EPUB
# and write them into src/content/chapitres/de-NNNN.md (body + statut: traduit).
#
# The Sammelband EPUBs contain 50 text files (index_split_*.xhtml) interleaved with
# 50 cover pages. The toc.ncx points to cover files only, so the reliable mapping is
# the German title found at the top of each text file, matched against the
# originalTitle of each chapter markdown file. The verified table below is the
# definitive result of that match (also cross-checked against the German EPUB).
Add-Type -AssemblyName System.IO.Compression.FileSystem

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$siteRoot    = Join-Path $scriptRoot '..'
$downloads   = 'C:\Users\Marc\Downloads\Perry Rhodan Sammelband'
$frEpub      = (Get-ChildItem -LiteralPath $downloads -Filter '*.epub' | Where-Object { $_.Name -like '*French*' }).FullName
$deEpub      = (Get-ChildItem -LiteralPath (Join-Path $downloads 'Perry Rhodan Sammelband') -Filter '*.epub' | Where-Object { $_.Name -match '0600-0649' }).FullName
$chapitresDir = Join-Path $siteRoot 'src\content\chapitres'

# Verified PR -> index_split text file (from title matching, both EPUBs)
$mapping = @{
  600='020'; 601='042'; 602='064'; 603='086'; 604='090'; 605='092'; 606='094'; 607='096'; 608='098'; 609='001'
  610='002'; 611='004'; 612='006'; 613='008'; 614='010'; 615='012'; 616='014'; 617='016'; 618='018'; 619='022'
  620='024'; 621='026'; 622='028'; 623='030'; 624='032'; 625='034'; 626='036'; 627='038'; 628='040'; 629='044'
  630='046'; 631='048'; 632='050'; 633='052'; 634='054'; 635='056'; 636='058'; 637='060'; 638='062'; 639='066'
  640='068'; 641='070'; 642='072'; 643='074'; 644='076'; 645='078'; 646='080'; 647='082'; 648='084'; 649='088'
}

function Get-TextEntry($zip, [string]$fullName) {
  $e = $zip.Entries | Where-Object { $_.FullName -eq $fullName }
  if (-not $e) { return $null }
  $ms = New-Object System.IO.MemoryStream
  $s = $e.Open(); $s.CopyTo($ms); $s.Close()
  return [System.Text.Encoding]::UTF8.GetString($ms.ToArray())
}

function Get-FirstLine([string]$xhtml) {
  $m = [regex]::Match($xhtml, '<p[^>]*>\s*([^<]{1,120})')
  if (-not $m.Success) { return '' }
  return $m.Groups[1].Value.Trim()
}

function Normalize([string]$s) {
  if (-not $s) { return '' }
  $s = $s.ToLowerInvariant()
  $s = $s -replace 'ä', 'a'
  $s = $s -replace 'ö', 'o'
  $s = $s -replace 'ü', 'u'
  $s = $s -replace 'ß', 'ss'
  $s = $s -replace '[^a-z0-9]', ''
  return $s
}

function Get-BodyToMarkdown([string]$xhtml) {
  $body = [regex]::Match($xhtml, '<body[^>]*>(.*)</body>', 'Singleline').Groups[1].Value
  $paras = New-Object System.Collections.Generic.List[string]
  $pos = 0
  while ($pos -lt $body.Length) {
    $m = [regex]::Match($body.Substring($pos), '<p[^>]*>(.*?)</p>|<p/>')
    if (-not $m.Success) { break }
    $pos += $m.Index + $m.Length
    if ($m.Value -eq '<p/>') { $paras.Add(''); continue }
    $inner = $m.Groups[1].Value
    $inner = $inner -replace '<[^>]+>', ''
    $inner = $inner -replace '&amp;', '&'
    $inner = $inner -replace '&lt;', '<'
    $inner = $inner -replace '&gt;', '>'
    $inner = $inner -replace '&quot;', '"'
    $inner = $inner -replace '&#39;|&apos;', "'"
    $inner = $inner -replace '&#160;|&nbsp;', ' '
    $paras.Add($inner)
  }
  # Drop the opening header block: title, subtitle, "par ..." (3 non-empty paragraphs)
  $nonEmpty = 0
  $start = 0
  for ($i = 0; $i -lt $paras.Count; $i++) {
    if ($paras[$i].Trim() -eq '') { continue }
    $nonEmpty++
    if ($nonEmpty -eq 3) { $start = $i + 1; break }
  }
  while ($start -lt $paras.Count -and $paras[$start].Trim() -eq '') { $start++ }

  $lines = New-Object System.Collections.Generic.List[string]
  for ($i = $start; $i -lt $paras.Count; $i++) {
    $t = $paras[$i].Trim()
    if ($t -eq '') { $lines.Add(''); continue }
    if ($t -eq '*') { $lines.Add('* * *'); continue }
    $lines.Add($t)
  }
  $out = New-Object System.Collections.Generic.List[string]
  $prevBlank = $false
  foreach ($l in $lines) {
    if ($l -eq '') {
      if (-not $prevBlank) { $out.Add('') }
      $prevBlank = $true
    } else {
      $out.Add($l)
      $prevBlank = $false
    }
  }
  return ($out -join "`n")
}

$archiveFr = [System.IO.Compression.ZipFile]::OpenRead($frEpub)
$archiveDe = [System.IO.Compression.ZipFile]::OpenRead($deEpub)
try {
  $written = 0
  foreach ($issue in ($mapping.Keys | Sort-Object)) {
    $num = $issue.ToString('0000')
    $slug = "de-$num"
    $mdPath = Join-Path $chapitresDir "$slug.md"
    if (-not (Test-Path -LiteralPath $mdPath)) { Write-Output "MISSING $mdPath"; continue }

    $split = $mapping[$issue]
    $frText = Get-TextEntry $archiveFr "OEBPS/Text/index_split_$split.xhtml"
    $deText = Get-TextEntry $archiveDe "OEBPS/Text/index_split_$split.xhtml"
    if (-not $frText) { Write-Output "NO FR CONTENT for $slug"; continue }

    $deFirst = Get-FirstLine $deText
    $frFirst = Get-FirstLine $frText
    if ($frFirst -eq '') { Write-Output "EMPTY first line for $slug"; continue }
    if ((Normalize $deFirst) -eq (Normalize $frFirst)) { Write-Output "WARN: identical header for $slug" }

    $body = Get-BodyToMarkdown $frText

    $existing = Get-Content -LiteralPath $mdPath -Raw -Encoding UTF8
    $fmMatch = [regex]::Match($existing, '(?s)^(---\r?\n.*?\r?\n---)\r?\n')
    if (-not $fmMatch.Success) { Write-Output "NO FRONTMATTER in $mdPath"; continue }
    $fm = $fmMatch.Groups[1].Value
    $fm = ($fm -replace '(?m)^statut: .*$', 'statut: traduit') -replace '\r', ''

    $md = $fm + "`n`n" + $body + "`n"
    [System.IO.File]::WriteAllText($mdPath, $md, (New-Object System.Text.UTF8Encoding($false)))
    Write-Output "WRITTEN $slug  (split_$split, fr='$frFirst', de='$deFirst', body=$($body.Length) chars)"
    $written++
  }
  Write-Output "DONE. $written chapters written."
}
finally {
  $archiveFr.Dispose()
  $archiveDe.Dispose()
}
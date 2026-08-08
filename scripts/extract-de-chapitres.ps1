# Extract German Perry Rhodan chapters from the Sammelband EPUBs into the site content.
# Generates: src/content/chapitres/de-NNNN.md (frontmatter + "WIP") and public/images/covers/de-NNNN.jpg
#
# Cycle info follows http://rhodan.stellarque.com/perryrhodan/listezyklus.php
Add-Type -AssemblyName System.IO.Compression.FileSystem

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$siteRoot    = Join-Path $scriptRoot '..'
$srcDir      = "C:\Users\Marc\Downloads\Perry Rhodan Sammelband\Perry Rhodan Sammelband"
$chapitresDir = Join-Path $siteRoot 'src\content\chapitres'
$coversDir    = Join-Path $siteRoot 'public\images\covers'
New-Item -ItemType Directory -Force -Path $chapitresDir | Out-Null
New-Item -ItemType Directory -Force -Path $coversDir    | Out-Null

$cycles = @(
  @{ n = 10; start = 600;  end = 649 },
  @{ n = 18; start = 1200; end = 1299 },
  @{ n = 19; start = 1300; end = 1349 },
  @{ n = 20; start = 1350; end = 1399 },
  @{ n = 21; start = 1400; end = 1499 },
  @{ n = 22; start = 1500; end = 1599 },
  @{ n = 23; start = 1600; end = 1649 },
  @{ n = 24; start = 1650; end = 1699 },
  @{ n = 25; start = 1700; end = 1749 },
  @{ n = 26; start = 1750; end = 1799 },
  @{ n = 27; start = 1800; end = 1875 },
  @{ n = 28; start = 1876; end = 1899 },
  @{ n = 29; start = 1900; end = 1949 },
  @{ n = 30; start = 1950; end = 1999 },
  @{ n = 31; start = 2000; end = 2099 },
  @{ n = 32; start = 2100; end = 2199 },
  @{ n = 33; start = 2200; end = 2299 },
  @{ n = 34; start = 2300; end = 2399 },
  @{ n = 35; start = 2400; end = 2499 },
  @{ n = 36; start = 2500; end = 2599 },
  @{ n = 37; start = 2600; end = 2699 },
  @{ n = 38; start = 2700; end = 2799 },
  @{ n = 39; start = 2800; end = 2874 },
  @{ n = 40; start = 2875; end = 2899 },
  @{ n = 41; start = 2900; end = 2999 },
  @{ n = 42; start = 3000; end = 3051 }
)

function Get-Cycle([int]$issue) {
  foreach ($c in $cycles) {
    if ($issue -ge $c.start -and $issue -le $c.end) { return $c.n }
  }
  return $null
}

# Anchors (documented German PR weekly dates)
# PR 2000 = Friday 1999-12-31 ; PR 2800 = Friday 2015-04-17 ; PR 2900 = Friday 2017-03-17
$anchorB1 = [datetime]"1999-12-31"   # for 2000-2799
$anchorB2 = [datetime]"2015-04-17"   # for 2800-2899
$anchorC  = [datetime]"2017-03-17"   # for 2900-3051

function Get-DateB([int]$issue) {
  if ($issue -ge 2800) { return $anchorB2.AddDays(($issue - 2800) * 7).ToString('yyyy-MM-dd') }
  return $anchorB1.AddDays(($issue - 2000) * 7).ToString('yyyy-MM-dd')
}
function Get-DateC([int]$issue) { return $anchorC.AddDays(($issue - 2900) * 7).ToString('yyyy-MM-dd') }

function Escape-Yaml([string]$s) {
  $s = $s -replace '\\', '\\'
  $s = $s -replace '"', '\"'
  return $s
}

function Write-Chapter([int]$issue, [string]$germanTitle, [string]$author, [string]$parution, $coverBytes, [string]$coverExt) {
  $cycle = Get-Cycle $issue
  if (-not $cycle) { Write-Output "SKIP issue $issue : no cycle"; return }
  $num = $issue.ToString('0000')
  $slug = "de-$num"
  $title = "$num - $germanTitle"
  $md = "---`n" +
        "title: `"$(Escape-Yaml $title)`"`n" +
        "cycleNumber: $cycle`n" +
        "chapterNumber: $issue`n" +
        "type: translation`n" +
        "originalTitle: `"$(Escape-Yaml $germanTitle)`"`n" +
        "cover: `"/images/covers/$slug.jpg`"`n" +
        "auteur: `"$(Escape-Yaml $author)`"`n" +
        "parution: `"$parution`"`n" +
        "---`n`nWIP`n"
  [System.IO.File]::WriteAllText((Join-Path $chapitresDir "$slug.md"), $md, (New-Object System.Text.UTF8Encoding($false)))
  if ($coverBytes -and $coverBytes.Length -gt 0) {
    $ext = if ($coverExt) { $coverExt } else { 'jpg' }
    [System.IO.File]::WriteAllBytes((Join-Path $coversDir "$slug.$ext"), $coverBytes)
  }
}

function Get-CoverBytes($archive, [string]$path) {
  $en = $archive.GetEntry($path)
  if ($en) {
    $ms = New-Object System.IO.MemoryStream
    $s = $en.Open(); $s.CopyTo($ms); $s.Close()
    $b = $ms.ToArray(); $ms.Dispose()
    return $b
  }
  return $null
}

$created = 0
$epubs = Get-ChildItem -LiteralPath $srcDir -Filter "*.epub" | Where-Object { $_.Name -notlike "*French*" } | Sort-Object Name

foreach ($epub in $epubs) {
  Write-Output "=== $($epub.Name.Substring(0, [Math]::Min(60, $epub.Name.Length))) ==="
  $archive = [System.IO.Compression.ZipFile]::OpenRead($epub.FullName)
  $entries = @($archive.Entries | ForEach-Object { $_.FullName })

  $hasMisc = $false
  $miscEntries = @()
  foreach ($en in $entries) { if ($en -like "OEBPS/Misc/*.opf") { $hasMisc = $true; $miscEntries += $en } }

  $hasSubOpf = $false
  foreach ($en in $entries) { if ($en -match "^\d+/(OEBPS/)?content\.opf$") { $hasSubOpf = $true; break } }

  if ($hasMisc) {
    foreach ($m in $miscEntries) {
      $e = $archive.GetEntry($m)
      $rd = New-Object System.IO.StreamReader($e.Open())
      $t = $rd.ReadToEnd(); $rd.Close()
      $issue = $null; $title = ''; $author = ''; $date = ''; $coverRef = ''
      if ($t -match 'calibre:series_index" content="([^"]+)"') { $issue = [int][double]$matches[1] }
      if ($t -match '<dc:title>([^<]+)</dc:title>') { $title = $matches[1].Trim() }
      if ($t -match '<dc:creator[^>]*>([^<]+)</dc:creator>') { $author = $matches[1].Trim() }
      if ($t -match '<dc:date>([^<]+)</dc:date>') { $date = ([datetime]$matches[1]).ToString('yyyy-MM-dd') }
      if ($t -match '<item href="(Pictures/[^"]+)"[^>]*id="id2"') { $coverRef = $matches[1] }
      if (-not $issue) { continue }
      $title = [regex]::Replace($title, '^\d{3,4}\s*-\s*', '')
      $coverBytes = $null; $coverExt = 'jpg'
      if ($coverRef) {
        $base = [System.IO.Path]::GetFileName($coverRef)
        $coverBytes = Get-CoverBytes $archive "OEBPS/Images/$base"
        if ($coverBytes) { $coverExt = [System.IO.Path]::GetExtension($base).TrimStart('.').ToLower() }
      }
      Write-Chapter $issue $title $author $date $coverBytes $coverExt
      $created++
    }
  }
  elseif ($hasSubOpf) {
    $subs = @()
    foreach ($en in $entries) { if ($en -match "^\d+/(OEBPS/)?content\.opf$") { $subs += $en } }
    foreach ($s in $subs) {
      $folder = ($s -split '/')[0]
      $e = $archive.GetEntry($s)
      $rd = New-Object System.IO.StreamReader($e.Open())
      $t = $rd.ReadToEnd(); $rd.Close()
      $issue = $null; $title = ''; $author = ''
      if ($t -match 'calibre:series_index" content="([^"]+)"') { $issue = [int][double]$matches[1] }
      if ($t -match '<dc:title>([^<]+)</dc:title>') { $title = $matches[1].Trim() }
      if ($t -match '<dc:creator[^>]*>([^<]+)</dc:creator>') { $author = $matches[1].Trim() }
      if (-not $issue) { continue }
      $parution = Get-DateC $issue
      $coverBytes = $null; $coverExt = 'jpg'
      $pat = "^$([regex]::Escape($folder))/"
      $best = $null
      foreach ($en in $entries) {
        if ($en -match $pat -and $en -match "cover\d*\.(jpg|jpeg|png)$") {
          if (-not $best -or $en.Length -lt $best.Length) { $best = $en }
        }
      }
      if ($best) {
        $coverBytes = Get-CoverBytes $archive $best
        if ($coverBytes) { $coverExt = [System.IO.Path]::GetExtension($best).TrimStart('.').ToLower() }
      }
      Write-Chapter $issue $title $author $parution $coverBytes $coverExt
      $created++
    }
  }
  else {
    $ncx = $archive.GetEntry("OEBPS/toc.ncx")
    if (-not $ncx) { $archive.Dispose(); Write-Output "  (no toc.ncx, skip)"; continue }
    $rd = New-Object System.IO.StreamReader($ncx.Open())
    $t = $rd.ReadToEnd(); $rd.Close()
    $matches = [regex]::Matches($t, '<text>\s*(?:Perry|PR)\s+(\d{4})\s*[\-\u2013]\s*(.+?)\s+by\s+(.+?)\s*</text>')
    foreach ($m in $matches) {
      $issue = [int]$m.Groups[1].Value
      $title = $m.Groups[2].Value.Trim()
      $author = $m.Groups[3].Value.Trim()
      $parution = Get-DateB $issue
      $coverBytes = Get-CoverBytes $archive "OEBPS/Images/Cover$issue.jpg"
      $coverExt = 'jpg'
      Write-Chapter $issue $title $author $parution $coverBytes $coverExt
      $created++
    }
    # some labels use "von" as the author separator instead of "by"
    $vonMatches = [regex]::Matches($t, '<text>\s*(?:Perry|PR)\s+(\d{4})\s*[\-\u2013]\s*(.+?)\s+von\s+(.+?)\s*</text>')
    foreach ($m in $vonMatches) {
      $issue = [int]$m.Groups[1].Value
      if (Test-Path -LiteralPath (Join-Path $chapitresDir ("de-{0}.md" -f $issue.ToString('0000')))) { continue }
      $title = $m.Groups[2].Value.Trim()
      $author = $m.Groups[3].Value.Trim()
      $parution = Get-DateB $issue
      $coverBytes = Get-CoverBytes $archive "OEBPS/Images/Cover$issue.jpg"
      $coverExt = 'jpg'
      Write-Chapter $issue $title $author $parution $coverBytes $coverExt
      $created++
    }
    # PR 2600 is missing from the #27 toc.ncx but the cover exists
    if (-not (Test-Path -LiteralPath (Join-Path $chapitresDir 'de-2600.md'))) {
      $coverBytes = Get-CoverBytes $archive "OEBPS/Images/Cover2600.jpg"
      Write-Chapter 2600 'Das Thanatos-Programm' 'Uwe Anton' (Get-DateB 2600) $coverBytes 'jpg'
      $created++
    }
  }
  $archive.Dispose()
}

Write-Output "DONE. Created $created chapter files."

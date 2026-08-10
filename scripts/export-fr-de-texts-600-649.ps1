# Export FR and DE chapter texts as plain text (one paragraph per line) for
# translation verification, plus a paragraph-alignment report.
#
# Output: C:\Users\Marc\AppData\Local\Temp\opencode\pr-check\
#   NNNN-fr.txt   : French paragraphs (one per line)
#   NNNN-de.txt   : German paragraphs (one per line)
#   NNNN-align.tsv: DE paragraph index, FR paragraph index, similarity (0..1),
#                   flagged when no good counterpart exists
#   report.txt    : per-chapter summary
Add-Type -AssemblyName System.IO.Compression.FileSystem

$outDir = 'C:\Users\Marc\AppData\Local\Temp\opencode\pr-check'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$downloads = 'C:\Users\Marc\Downloads\Perry Rhodan Sammelband'
$frEpub = (Get-ChildItem -LiteralPath $downloads -Filter '*.epub' | Where-Object { $_.Name -like '*French*' }).FullName
$deEpub = (Get-ChildItem -LiteralPath (Join-Path $downloads 'Perry Rhodan Sammelband') -Filter '*.epub' | Where-Object { $_.Name -match '0600-0649' }).FullName

$mapping = @{
  600='020'; 601='042'; 602='064'; 603='086'; 604='090'; 605='092'; 606='094'; 607='096'; 608='098'; 609='001'
  610='002'; 611='004'; 612='006'; 613='008'; 614='010'; 615='012'; 616='014'; 617='016'; 618='018'; 619='022'
  620='024'; 621='026'; 622='028'; 623='030'; 624='032'; 625='034'; 626='036'; 627='038'; 628='040'; 629='044'
  630='046'; 631='048'; 632='050'; 633='052'; 634='054'; 635='056'; 636='058'; 637='060'; 638='062'; 639='066'
  640='068'; 641='070'; 642='072'; 643='074'; 644='076'; 645='078'; 646='080'; 647='082'; 648='084'; 649='088'
}

function Get-Paragraphs([string]$xhtml) {
  $body = [regex]::Match($xhtml, '<body[^>]*>(.*)</body>', 'Singleline').Groups[1].Value
  $paras = New-Object System.Collections.Generic.List[string]
  $pos = 0
  while ($pos -lt $body.Length) {
    $m = [regex]::Match($body.Substring($pos), '<p[^>]*>(.*?)</p>|<p/>')
    if (-not $m.Success) { break }
    $pos += $m.Index + $m.Length
    if ($m.Value -eq '<p/>') { $paras.Add(''); continue }
    $inner = $m.Groups[1].Value -replace '<[^>]+>', ''
    $inner = $inner -replace '&amp;', '&' -replace '&lt;', '<' -replace '&gt;', '>' -replace '&quot;', '"' -replace '&#39;|&apos;', "'" -replace '&#160;|&nbsp;', ' '
    $paras.Add($inner)
  }
  return $paras
}

function Get-TextEntry($zip, [string]$fullName) {
  $e = $zip.Entries | Where-Object { $_.FullName -eq $fullName }
  if (-not $e) { return $null }
  $ms = New-Object System.IO.MemoryStream
  $s = $e.Open(); $s.CopyTo($ms); $s.Close()
  return [System.Text.Encoding]::UTF8.GetString($ms.ToArray())
}

function Get-Tokens([string]$s) {
  $s = $s.ToLowerInvariant()
  $s = $s -replace 'ä', 'a' -replace 'ö', 'o' -replace 'ü', 'u' -replace 'ß', 'ss'
  return [regex]::Matches($s, '[a-z0-9]+') | ForEach-Object { $_.Value }
}

function Get-Sim([string]$a, [string]$b) {
  $ta = Get-Tokens $a
  $tb = Get-Tokens $b
  if ($ta.Count -eq 0 -or $tb.Count -eq 0) { return 0.0 }
  $set = @{}
  foreach ($t in $ta) { if ($set.ContainsKey($t)) { $set[$t]++ } else { $set[$t] = 1 } }
  $same = 0
  foreach ($t in $tb) { if ($set[$t] -gt 0) { $same++; $set[$t]-- } }
  return [double]$same / [math]::Max($ta.Count, $tb.Count)
}

$archFr = [System.IO.Compression.ZipFile]::OpenRead($frEpub)
$archDe = [System.IO.Compression.ZipFile]::OpenRead($deEpub)
try {
  $reportLines = New-Object System.Collections.Generic.List[string]
  $reportLines.Add("PR`tDEparas`tFRparas`tflaggedDE`tflaggedFR`tsimMedian")
  foreach ($issue in ($mapping.Keys | Sort-Object)) {
    $split = $mapping[$issue]
    $frText = Get-TextEntry $archFr "OEBPS/Text/index_split_$split.xhtml"
    $deText = Get-TextEntry $archDe "OEBPS/Text/index_split_$split.xhtml"
    $frParas = Get-Paragraphs $frText
    $deParas = Get-Paragraphs $deText

    [System.IO.File]::WriteAllLines((Join-Path $outDir "$issue-fr.txt"), $frParas, (New-Object System.Text.UTF8Encoding($false)))
    [System.IO.File]::WriteAllLines((Join-Path $outDir "$issue-de.txt"), $deParas, (New-Object System.Text.UTF8Encoding($false)))

    # Alignment: for each DE paragraph find best FR counterpart; flag both sides
    $flaggedDe = 0
    $sims = New-Object System.Collections.Generic.List[double]
    $alignLines = New-Object System.Collections.Generic.List[string]
    for ($i = 0; $i -lt $deParas.Count; $i++) {
      $de = $deParas[$i]
      if ($de.Trim() -eq '') { continue }
      $best = 0.0; $bestJ = -1
      for ($j = 0; $j -lt $frParas.Count; $j++) {
        $sim = Get-Sim $de $frParas[$j]
        if ($sim -gt $best) { $best = $sim; $bestJ = $j }
      }
      $sims.Add($best)
      $flag = ''
      if ($best -lt 0.4) { $flag = 'LOW'; $flaggedDe++ }
      $alignLines.Add("$i`t$bestJ`t$([math]::Round($best,2))`t$flag")
    }
    $simsArr = @($sims | Sort-Object)
    $median = [math]::Round($simsArr[[int]($simsArr.Count / 2)], 2)
    [System.IO.File]::WriteAllLines((Join-Path $outDir "$issue-align.tsv"), $alignLines, (New-Object System.Text.UTF8Encoding($false)))
    $reportLines.Add("$issue`t$($deParas.Count)`t$($frParas.Count)`t$flaggedDe`t-`t$median")
    Write-Output "EXPORT $issue (DE=$($deParas.Count) FR=$($frParas.Count) flaggedDE=$flaggedDe median=$median)"
  }
  [System.IO.File]::WriteAllLines((Join-Path $outDir 'report.tsv'), $reportLines, (New-Object System.Text.UTF8Encoding($false)))
  Write-Output "DONE. Files in $outDir"
}
finally {
  $archFr.Dispose(); $archDe.Dispose()
}
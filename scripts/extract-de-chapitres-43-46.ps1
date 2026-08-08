# Extract German chapters 3100-3399 (cycles 43-46) from cycles pages on rhodan.stellarque.com
# No covers exist for this range (no EPUBs) - cover field omitted.
$scriptRoot = if ($MyInvocation.MyCommand.Path) { Split-Path -Parent $MyInvocation.MyCommand.Path } else { (Get-Location).Path }
$siteRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptRoot '..'))
$chapitresDir = Join-Path $siteRoot 'src\content\chapitres'
New-Item -ItemType Directory -Force -Path $chapitresDir | Out-Null

$cycles = @(
  @{ n = 43; start = 3100; end = 3199 },
  @{ n = 44; start = 3200; end = 3299 },
  @{ n = 45; start = 3300; end = 3349 },
  @{ n = 46; start = 3350; end = 3399 }
)
function Get-Cycle([int]$issue) {
  foreach ($c in $cycles) { if ($issue -ge $c.start -and $issue -le $c.end) { return $c.n } }
  return $null
}

$anchorC = [datetime]"2017-03-17"
function Get-DateC([int]$issue) { return $anchorC.AddDays(($issue - 2900) * 7).ToString('yyyy-MM-dd') }

function Escape-Yaml([string]$s) {
  $s = $s -replace '\\', '\\'
  $s = $s -replace '"', '\"'
  return $s
}

function Fetch-Fascicules([int]$cycleNum, [string]$url) {
  $wc = New-Object System.Net.WebClient
  $bytes = $wc.DownloadData($url)
  $wc.Dispose()
  $utf8strict = New-Object System.Text.UTF8Encoding($false, $true)
  try { $html = $utf8strict.GetString($bytes) } catch { $html = [System.Text.Encoding]::GetEncoding(28591).GetString($bytes) }
  $items = @()
  # Split by <tr valign="top"> rows; each carries: <div align="center">NNNN</div> ... <a href=...>Title</a> ... <font size="1">Auteur</font>
  $rows = [regex]::Matches($html, '<tr\s+valign="top">(.*?)</tr>', [System.Text.RegularExpressions.RegexOptions]::Singleline)
  foreach ($row in $rows) {
    $body = $row.Groups[1].Value
    $numMatch = [regex]::Match($body, 'align="center">(\d{4})')
    if (-not $numMatch.Success) { continue }
    $titleMatch = [regex]::Match($body, '<a\s+href="[^"]*">([^<]+)</a>')
    # prefer the title link that is NOT a list anchor (#fasc / #rg); take the longest <a> text
    $at = [regex]::Matches($body, '<a\s+href="[^"]*">([^<]+)</a>')
    $title = ''
    foreach ($a in $at) { if ($a.Groups[1].Value.Length -gt $title.Length) { $title = $a.Groups[1].Value } }
    $authorMatch = [regex]::Match($body, '<font\s+size="1">(.*?)</font>', [System.Text.RegularExpressions.RegexOptions]::Singleline)
    $author = if ($authorMatch.Success) { $authorMatch.Groups[1].Value } else { '' }
    $issue = [int]$numMatch.Groups[1].Value
    if (-not $title) { continue }
    $items += [PSCustomObject]@{
      Issue = $issue
      Title = ([System.Net.WebUtility]::HtmlDecode($title)).Trim()
      Author = ([System.Net.WebUtility]::HtmlDecode($author)).Trim()
    }
  }
  return $items
}

$all = @()
foreach ($c in $cycles) {
  $url = if ($c.n -le 44) { "http://rhodan.stellarque.com/perryrhodan/cycle_$($c.n).php" } else { "http://rhodan.stellarque.com/perryrhodan/cycle.php?init=$($c.n)" }
  Write-Output "=== cycle $($c.n) ==="
  $items = Fetch-Fascicules $c.n $url
  Write-Output "fetched $($items.Count) rows"
  foreach ($it in $items) { if ($it.Issue -ge $c.start -and $it.Issue -le $c.end) { $all += $it } }
}

$created = 0
foreach ($it in ($all | Sort-Object Issue -Unique)) {
  $cycle = Get-Cycle $it.Issue
  if (-not $cycle) { continue }
  $num = $it.Issue.ToString('0000')
  $slug = "de-$num"
  $title = "$num - $($it.Title)"
  $md = "---`n" +
        "title: `"$(Escape-Yaml $title)`"`n" +
        "cycleNumber: $cycle`n" +
        "chapterNumber: $($it.Issue)`n" +
        "type: translation`n" +
        "originalTitle: `"$(Escape-Yaml $it.Title)`"`n" +
        "auteur: `"$(Escape-Yaml $it.Author)`"`n" +
        "parution: `"$(Get-DateC $it.Issue)`"`n" +
        "---`n`nWIP`n"
  [System.IO.File]::WriteAllText((Join-Path $chapitresDir "$slug.md"), $md, (New-Object System.Text.UTF8Encoding($false)))
  $created++
}
Write-Output "DONE. Created $created chapters 3100-3399."
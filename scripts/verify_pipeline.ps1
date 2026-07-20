param(
    [string]$ApiBaseUrl = "http://localhost:8000/api/v1",
    [string]$PayloadPath = "sample-data/mes/lot_completed_sample.json",
    [string]$Bucket = "semiconductor-landing",
    [string]$Prefix = "mes/",
    [string]$Stream = "mes-events",
    [string]$DbUser = "sap_user",
    [string]$DbName = "semiconductor",
    [string]$DbTable = "mdm.lot_master",
    [string]$NormalizeSourcePrefix = "files/native",
    [string]$NormalizeOutputPrefix = "files/native/normalized",
    [switch]$IngestSample,
    [switch]$IngestAllSamples
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$sourceChecks = @(
    @{
        Name = "mes"
        Endpoint = "mes/events"
        PayloadPath = "sample-data/mes/lot_completed_sample.json"
        Prefix = "mes/"
        Stream = "mes-events"
        DbTable = "mdm.lot_master"
        DbQuery = "SELECT COUNT(*) FROM mdm.lot_master;"
    },
    @{
        Name = "erp"
        Endpoint = "erp/events"
        PayloadPath = "sample-data/erp/work_order_sample.json"
        Prefix = "erp/"
        Stream = "metadata-events"
        DbTable = "metadata.raw_events"
        DbQuery = "SELECT COUNT(*) FROM metadata.raw_events WHERE source = 'erp';"
    },
    @{
        Name = "equipment"
        Endpoint = "equipment/events"
        PayloadPath = "sample-data/equipment/equipment_event_sample.json"
        Prefix = "equipment/"
        Stream = "quality-events"
        DbTable = "metadata.raw_events"
        DbQuery = "SELECT COUNT(*) FROM metadata.raw_events WHERE source = 'equipment';"
    },
    @{
        Name = "plm"
        Endpoint = "plm/events"
        PayloadPath = "sample-data/plm/product_lifecycle_event_sample.json"
        Prefix = "plm/"
        Stream = "plm-events"
        DbTable = "metadata.raw_events"
        DbQuery = "SELECT COUNT(*) FROM metadata.raw_events WHERE source = 'plm';"
    }
)

$results = New-Object System.Collections.Generic.List[object]

function Add-Result {
    param(
        [string]$Name,
        [bool]$Passed,
        [string]$Details
    )

    $results.Add([PSCustomObject]@{
        Check = $Name
        Status = if ($Passed) { "PASS" } else { "FAIL" }
        Details = $Details
    })
}

function Invoke-Step {
    param(
        [scriptblock]$Command,
        [string]$StepName
    )

    try {
        $output = & $Command 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "$StepName failed: $output"
        }
        return ($output | Out-String).Trim()
    }
    catch {
        throw "$StepName failed: $($_.Exception.Message)"
    }
}

function Get-ExecutedCommand {
    $cmd = ".\\scripts\\verify_pipeline.ps1"
    if ($IngestSample) {
        $cmd += " -IngestSample"
    }
    if ($IngestAllSamples) {
        $cmd += " -IngestAllSamples"
    }
    if ($NormalizeSourcePrefix -ne "files/native") {
        $cmd += " -NormalizeSourcePrefix `"$NormalizeSourcePrefix`""
    }
    if ($NormalizeOutputPrefix -ne "files/native/normalized") {
        $cmd += " -NormalizeOutputPrefix `"$NormalizeOutputPrefix`""
    }
    return $cmd
}

function Get-PythonCommand {
    if ($env:VIRTUAL_ENV) {
        $venvPython = Join-Path $env:VIRTUAL_ENV "Scripts/python.exe"
        if (Test-Path -Path $venvPython) {
            return $venvPython
        }
    }
    return "python"
}

function Write-VerificationReport {
    param(
        [System.Collections.Generic.List[object]]$VerificationResults
    )

    $reportPath = Join-Path $repoRoot "docs/end_to_end_test_result.md"
    $executedCommand = Get-ExecutedCommand
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("# End-to-End Test Command and Latest Result")
    $lines.Add("")
    $lines.Add("Date: $timestamp")
    $lines.Add("")
    $lines.Add("## Command Executed")
    $lines.Add("")
    $lines.Add('```powershell')
    $lines.Add($executedCommand)
    $lines.Add('```')
    $lines.Add("")
    $lines.Add("## Result Returned")
    $lines.Add("")
    $lines.Add("| Check | Status | Details |")
    $lines.Add("|---|---|---|")

    foreach ($row in $VerificationResults) {
        $check = [string]$row.Check
        $status = [string]$row.Status
        $details = ([string]$row.Details).Replace("|", "\\|")
        $lines.Add("| $check | $status | $details |")
    }

    $lines.Add("")
    $lines.Add("## Save Future Runs To File")
    $lines.Add("")
    $lines.Add('```powershell')
    $lines.Add('.\\scripts\\verify_pipeline.ps1 -IngestAllSamples | Tee-Object -FilePath .\\docs\\end_to_end_test_latest.txt')
    $lines.Add('```')

    Set-Content -Path $reportPath -Value $lines -Encoding UTF8
}

try {
    Invoke-Step -StepName "docker compose ps" -Command { docker compose ps --format json } | Out-Null
    Add-Result -Name "Docker Compose reachable" -Passed $true -Details "docker compose is available"
}
catch {
    Add-Result -Name "Docker Compose reachable" -Passed $false -Details $_.Exception.Message
}

try {
    $statusCode = Invoke-Step -StepName "API readiness" -Command {
        curl.exe -sS -o NUL -w "%{http_code}" "$ApiBaseUrl/ready"
    }
    Add-Result -Name "API readiness" -Passed ($statusCode -eq "200") -Details "HTTP $statusCode"
}
catch {
    Add-Result -Name "API readiness" -Passed $false -Details $_.Exception.Message
}

if ($IngestSample) {
    try {
        $payloadToUse = if ([System.IO.Path]::IsPathRooted($PayloadPath)) {
            $PayloadPath
        }
        else {
            Join-Path $repoRoot $PayloadPath
        }

        if (-not (Test-Path -Path $payloadToUse)) {
            throw "Payload file not found at path: $payloadToUse"
        }

        $ingestCode = Invoke-Step -StepName "Sample ingestion" -Command {
            curl.exe -sS -o NUL -w "%{http_code}" -X POST "$ApiBaseUrl/mes/events" -H "Content-Type: application/json" --data-binary "@$payloadToUse"
        }

        Add-Result -Name "Sample ingestion" -Passed ($ingestCode -eq "202") -Details "HTTP $ingestCode"
    }
    catch {
        Add-Result -Name "Sample ingestion" -Passed $false -Details $_.Exception.Message
    }
}

if ($IngestAllSamples) {
    foreach ($source in $sourceChecks) {
        try {
            $payloadToUse = Join-Path $repoRoot $source.PayloadPath
            if (-not (Test-Path -Path $payloadToUse)) {
                throw "Payload file not found at path: $payloadToUse"
            }

            $ingestCode = Invoke-Step -StepName "Sample ingestion for $($source.Name)" -Command {
                curl.exe -sS -o NUL -w "%{http_code}" -X POST "$ApiBaseUrl/$($source.Endpoint)" -H "Content-Type: application/json" --data-binary "@$payloadToUse"
            }

            Add-Result -Name "Sample ingestion ($($source.Name))" -Passed ($ingestCode -eq "202") -Details "HTTP $ingestCode"
        }
        catch {
            Add-Result -Name "Sample ingestion ($($source.Name))" -Passed $false -Details $_.Exception.Message
        }
    }
}

if ($IngestAllSamples) {
    try {
        $pythonCmd = Get-PythonCommand
        $uploadScript = @"
from pathlib import Path
import boto3

bucket = r"$Bucket"
prefix = r"$NormalizeSourcePrefix".strip("/")

files = [
    r"sample-data/files/native/system_health_sample.xml",
    r"sample-data/files/native/work_orders_sample.csv",
    r"sample-data/files/native/driver_logs_sample.txt",
    r"sample-data/files/native/benchmark_sample.parquet",
]

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

for rel in files:
    path = Path(rel)
    if not path.exists():
        raise FileNotFoundError(f"Native sample not found: {path}")
    key = f"{prefix}/{path.name}" if prefix else path.name
    s3.put_object(Bucket=bucket, Key=key, Body=path.read_bytes())

print(f"uploaded={len(files)}")
"@

        Invoke-Step -StepName "Upload native files to S3" -Command {
            & $pythonCmd -c $uploadScript
        } | Out-Null

        $env:AWS_ENDPOINT_URL = "http://localhost:4566"
        $env:AWS_REGION = "us-east-1"
        $env:AWS_ACCESS_KEY_ID = "test"
        $env:AWS_SECRET_ACCESS_KEY = "test"

        Invoke-Step -StepName "Run S3 normalization script" -Command {
            & $pythonCmd "scripts/normalize_s3_files.py" --source file_multiformat --bucket $Bucket --source-prefix $NormalizeSourcePrefix --normalized-prefix $NormalizeOutputPrefix --format AUTO
        } | Out-Null

        $normalizedListRaw = Invoke-Step -StepName "List normalized objects" -Command {
            docker compose exec -T localstack awslocal s3 ls "s3://$Bucket/$NormalizeOutputPrefix/" --recursive
        }

        $normalizedLines = @($normalizedListRaw -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 })
        $normalizedCount = 0
        foreach ($line in $normalizedLines) {
            $parts = $line -split "\s+", 4
            if ($parts.Count -ge 4 -and $parts[3].EndsWith(".json")) {
                $normalizedCount++
            }
        }

        Add-Result -Name "Native normalization" -Passed ($normalizedCount -ge 4) -Details "Normalized $normalizedCount JSON object(s) under $NormalizeOutputPrefix"
    }
    catch {
        Add-Result -Name "Native normalization" -Passed $false -Details $_.Exception.Message
    }
}

try {
    Invoke-Step -StepName "S3 bucket check" -Command {
        docker compose exec -T localstack awslocal s3api head-bucket --bucket $Bucket
    } | Out-Null

    $s3ListRaw = Invoke-Step -StepName "S3 object listing" -Command {
        docker compose exec -T localstack awslocal s3 ls "s3://$Bucket" --recursive
    }

    $s3Lines = @($s3ListRaw -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 })
    $s3Count = 0

    foreach ($line in $s3Lines) {
        $parts = $line -split "\s+", 4
        if ($parts.Count -lt 4) {
            continue
        }

        $key = $parts[3]
        if ([string]::IsNullOrEmpty($Prefix) -or $key.StartsWith($Prefix)) {
            $s3Count++
        }
    }

    Add-Result -Name "S3 objects present" -Passed ($s3Count -gt 0) -Details "Found $s3Count object(s) under $Prefix"
}
catch {
    Add-Result -Name "S3 objects present" -Passed $false -Details $_.Exception.Message
}

foreach ($source in $sourceChecks) {
    try {
        $s3ListRaw = Invoke-Step -StepName "S3 object listing for $($source.Name)" -Command {
            docker compose exec -T localstack awslocal s3 ls "s3://$Bucket" --recursive
        }

        $s3Lines = @($s3ListRaw -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 })
        $s3Count = 0

        foreach ($line in $s3Lines) {
            $parts = $line -split "\s+", 4
            if ($parts.Count -lt 4) {
                continue
            }

            $key = $parts[3]
            if ($key.StartsWith($source.Prefix)) {
                $s3Count++
            }
        }

        Add-Result -Name "S3 objects ($($source.Name))" -Passed ($s3Count -gt 0) -Details "Found $s3Count object(s) under $($source.Prefix)"
    }
    catch {
        Add-Result -Name "S3 objects ($($source.Name))" -Passed $false -Details $_.Exception.Message
    }
}

try {
    $streamStatus = Invoke-Step -StepName "Kinesis stream status" -Command {
        docker compose exec -T localstack awslocal kinesis describe-stream --stream-name $Stream --query "StreamDescription.StreamStatus" --output text
    }

    $streamReady = ($streamStatus.Trim() -eq "ACTIVE")

    $shardId = Invoke-Step -StepName "Kinesis shard id" -Command {
        docker compose exec -T localstack awslocal kinesis describe-stream --stream-name $Stream --query "StreamDescription.Shards[0].ShardId" --output text
    }

    $iterator = Invoke-Step -StepName "Kinesis shard iterator" -Command {
        docker compose exec -T localstack awslocal kinesis get-shard-iterator --stream-name $Stream --shard-id $shardId --shard-iterator-type TRIM_HORIZON --query "ShardIterator" --output text
    }

    $recordsCountRaw = Invoke-Step -StepName "Kinesis records" -Command {
        docker compose exec -T localstack awslocal kinesis get-records --shard-iterator $iterator --limit 10 --query "length(Records)" --output text
    }

    $recordsCount = 0
    [void][int]::TryParse(($recordsCountRaw.Trim()), [ref]$recordsCount)
    Add-Result -Name "Kinesis stream data" -Passed ($streamReady -and $recordsCount -gt 0) -Details "Status=$streamStatus, Records=$recordsCount"
}
catch {
    Add-Result -Name "Kinesis stream data" -Passed $false -Details $_.Exception.Message
}

foreach ($source in $sourceChecks) {
    try {
        $streamStatus = Invoke-Step -StepName "Kinesis stream status for $($source.Name)" -Command {
            docker compose exec -T localstack awslocal kinesis describe-stream --stream-name $($source.Stream) --query "StreamDescription.StreamStatus" --output text
        }

        $streamReady = ($streamStatus.Trim() -eq "ACTIVE")

        $shardId = Invoke-Step -StepName "Kinesis shard id for $($source.Name)" -Command {
            docker compose exec -T localstack awslocal kinesis describe-stream --stream-name $($source.Stream) --query "StreamDescription.Shards[0].ShardId" --output text
        }

        $iterator = Invoke-Step -StepName "Kinesis shard iterator for $($source.Name)" -Command {
            docker compose exec -T localstack awslocal kinesis get-shard-iterator --stream-name $($source.Stream) --shard-id $shardId --shard-iterator-type TRIM_HORIZON --query "ShardIterator" --output text
        }

        $recordsCountRaw = Invoke-Step -StepName "Kinesis records for $($source.Name)" -Command {
            docker compose exec -T localstack awslocal kinesis get-records --shard-iterator $iterator --limit 10 --query "length(Records)" --output text
        }

        $recordsCount = 0
        [void][int]::TryParse(($recordsCountRaw.Trim()), [ref]$recordsCount)
        Add-Result -Name "Kinesis stream data ($($source.Name))" -Passed ($streamReady -and $recordsCount -gt 0) -Details "Status=$streamStatus, Records=$recordsCount"
    }
    catch {
        Add-Result -Name "Kinesis stream data ($($source.Name))" -Passed $false -Details $_.Exception.Message
    }
}

try {
    $dbReady = Invoke-Step -StepName "Postgres connectivity" -Command {
        docker compose exec -T postgres psql -U $DbUser -d $DbName -tAc "SELECT 1"
    }

    $tableExists = Invoke-Step -StepName "Postgres table existence" -Command {
        docker compose exec -T postgres psql -U $DbUser -d $DbName -tAc "SELECT to_regclass('$DbTable') IS NOT NULL;"
    }

    $rowCountRaw = Invoke-Step -StepName "Postgres row count" -Command {
        docker compose exec -T postgres psql -U $DbUser -d $DbName -tAc "SELECT COUNT(*) FROM $DbTable;"
    }

    $rowCount = 0
    [void][int]::TryParse(($rowCountRaw.Trim()), [ref]$rowCount)

    $dbCheckPass = (($dbReady.Trim() -eq "1") -and ($tableExists.Trim() -eq "t") -and ($rowCount -gt 0))
    Add-Result -Name "Postgres data" -Passed $dbCheckPass -Details "TableExists=$tableExists, Rows=$rowCount"
}
catch {
    Add-Result -Name "Postgres data" -Passed $false -Details $_.Exception.Message
}

foreach ($source in $sourceChecks) {
    try {
        $tableExists = Invoke-Step -StepName "Postgres table existence for $($source.Name)" -Command {
            docker compose exec -T postgres psql -U $DbUser -d $DbName -tAc "SELECT to_regclass('$($source.DbTable)') IS NOT NULL;"
        }

        $rowCountRaw = Invoke-Step -StepName "Postgres row count for $($source.Name)" -Command {
            docker compose exec -T postgres psql -U $DbUser -d $DbName -tAc $source.DbQuery
        }

        $rowCount = 0
        [void][int]::TryParse(($rowCountRaw.Trim()), [ref]$rowCount)
        $dbCheckPass = (($tableExists.Trim() -eq "t") -and ($rowCount -gt 0))

        Add-Result -Name "Postgres data ($($source.Name))" -Passed $dbCheckPass -Details "TableExists=$tableExists, Rows=$rowCount"
    }
    catch {
        Add-Result -Name "Postgres data ($($source.Name))" -Passed $false -Details $_.Exception.Message
    }
}

""
"Verification summary"
"===================="
$results | Format-Table -AutoSize

Write-VerificationReport -VerificationResults $results

$failed = $results | Where-Object { $_.Status -eq "FAIL" }
if (@($failed).Count -gt 0) {
    exit 1
}

exit 0

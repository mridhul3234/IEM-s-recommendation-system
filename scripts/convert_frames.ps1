# PowerShell script to convert JPEG frame sequence to WebP (Quality 60) if cwebp or ffmpeg is installed
param (
    [string]$InputDir = "..\frontend\public\iem_frames",
    [string]$Quality = "60"
)

if (Get-Command cwebp -ErrorAction SilentlyContinue) {
    Write-Host "Converting JPG frames to WebP using cwebp..."
    Get-ChildItem -Path $InputDir -Filter "*.jpg" | ForEach-Object {
        $webpName = $_.FullName -replace '\.jpg$', '.webp'
        cwebp -q $Quality $_.FullName -o $webpName
    }
    Write-Host "WebP conversion complete."
} elseif (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Host "Converting JPG frames to WebP using ffmpeg..."
    Get-ChildItem -Path $InputDir -Filter "*.jpg" | ForEach-Object {
        $webpName = $_.FullName -replace '\.jpg$', '.webp'
        ffmpeg -i $_.FullName -q:v $Quality $webpName -y -loglevel error
    }
    Write-Host "WebP conversion complete."
} else {
    Write-Host "Neither cwebp nor ffmpeg was found on PATH. Frame conversion skipped."
}

# Send UDP syslog lines (Windows PowerShell)
param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 514
)

function Send-Syslog([string]$Message) {
  $udp = New-Object System.Net.Sockets.UdpClient
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($Message)
  $udp.Send($bytes, $bytes.Length, $HostName, $Port) | Out-Null
  $udp.Close()
  Write-Host "sent: $Message"
}

Send-Syslog '<134>Aug 20 12:44:56 fw01 vendor=demo product=ngfw action=deny src=10.0.1.10 dst=8.8.8.8 spt=5353 dpt=53 proto=udp msg=DNS_blocked policy=Block-DNS'
Send-Syslog '<190>Aug 20 13:01:02 r1 if=ge-0/0/1 event=link-down mac=aa:bb:cc:dd:ee:ff reason=carrier-loss'
Write-Host "Done. Check UI within ~1 minute."

param (
    [string]$algo = "SPYCC"
)

venv\Scripts\activate.ps1
(Get-Content ops\debug.ps1) -replace "`"(.*?)`"", "`"$algo`"" | Set-Content ops\debug.ps1
code ./$algo
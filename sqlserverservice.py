import subprocess
import time
import sys
from pathlib import Path

def run_powershell_command(command, as_admin=False):
    """Run PowerShell command and return output"""
    try:
        if as_admin:
            command = f'Start-Process powershell -Verb RunAs -ArgumentList "-Command {command}"'
        
        result = subprocess.run(
            ['powershell', '-Command', command],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return None

def fix_sql_service():
    print("=== SQL Server Service Fix ===\n")
    
    # 1. Check if running as administrator
    admin_check = run_powershell_command("[bool](([System.Security.Principal.WindowsIdentity]::GetCurrent()).groups -match 'S-1-5-32-544')")
    if not admin_check or 'True' not in admin_check:
        print("Please run VS Code as Administrator!")
        print("Right-click VS Code -> Run as administrator")
        return
    
    # 2. Verify SQL Server installation
    print("\nVerifying SQL Server installation...")
    install_check = run_powershell_command("""
        Get-WmiObject -Class Win32_Service | 
        Where-Object {$_.Name -eq 'MSSQL$SQLEXPRESS'} | 
        Select-Object Name, StartName, State
    """)
    print(f"Installation status: {install_check}")
    
    # 3. Stop and reconfigure services with elevated privileges
    services = ['MSSQL$SQLEXPRESS', 'SQLBrowser', 'SQLWriter', 'SQLTELEMETRY$SQLEXPRESS']
    
    for service in services:
        print(f"\nHandling service: {service}")
        # Stop service with elevated privileges
        stop_cmd = f"Stop-Service -Name '{service}' -Force"
        run_powershell_command(stop_cmd, as_admin=True)
        
        if service == 'MSSQL$SQLEXPRESS':
            print("Reconfiguring SQL Server service...")
            config_cmd = f"""
            $securePass = ConvertTo-SecureString -String '' -AsPlainText -Force
            $cred = New-Object System.Management.Automation.PSCredential ('NT Service\\{service}', $securePass)
            $params = @{{
                Name = '{service}'
                Credential = $cred
                StartupType = 'Automatic'
            }}
            Set-Service @params
            """
            run_powershell_command(config_cmd, as_admin=True)
    
    # 4. Start services in correct order with elevated privileges
    time.sleep(2)
    print("\nStarting services...")
    for service in reversed(services):
        print(f"Starting {service}...")
        start_cmd = f"Start-Service -Name '{service}'"
        run_powershell_command(start_cmd, as_admin=True)
        time.sleep(2)
        
        # Check service status
        status_cmd = f"(Get-Service -Name '{service}').Status"
        status = run_powershell_command(status_cmd)
        print(f"Status: {status}")
    
    # 5. Final verification
    print("\nPerforming final verification...")
    verify_cmd = """
    $service = Get-Service -Name 'MSSQL$SQLEXPRESS' -ErrorAction SilentlyContinue
    if ($service) {
        Write-Output "Service Name: $($service.Name)"
        Write-Output "Status: $($service.Status)"
        Write-Output "Start Type: $($service.StartType)"
    } else {
        Write-Output "SQL Server service not found"
    }
    """
    final_status = run_powershell_command(verify_cmd)
    print(final_status)

if __name__ == "__main__":
    fix_sql_service()
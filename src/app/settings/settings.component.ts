import { Component, OnInit } from '@angular/core';
import { FormGroup, FormControl, Validators, FormBuilder } from '@angular/forms';
import { SettingsService } from '../services/settings.service';
import Swal from 'sweetalert2';

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})
export class SettingsComponent implements OnInit {
  settingsForm: FormGroup;
  settings: any[] = [];
  settingsObject: any;
  isAdmin: string = localStorage.getItem('isAdmin') || '';
  testConnectSucess: string;

  constructor(private fb: FormBuilder, private settingsService: SettingsService) {
    this.settingsForm = this.fb.group({

      ssh_port: new FormControl('', Validators.required),
      rsyslog_port: new FormControl('', Validators.required),
      grafana_port: new FormControl('3000', Validators.required),
      company_name: new FormControl('', Validators.required)
    })
  }

  ngOnInit(): void {
    this.getSettings();
  }

  getSettings() {
    this.settingsService.getSettings().subscribe((res: any) => {
      this.settingsObject = res.settings_data;
      let value = {
        ssh_port: parseInt(res.settings_data.ssh_port),
        rsyslog_port: parseInt(res.settings_data.rsyslog_port),
        grafana_port: parseInt(res.settings_data.grafana_port),
        company_name: res.settings_data.company_name
      }
      this.settingsForm.setValue(value);
    })
  }

  saveSettings() {
    let value = {
      "ssh_port": parseInt(this.settingsForm.value['ssh_port']),
      "rsyslog_port": parseInt(this.settingsForm.value['rsyslog_port']),
      "grafana_port": parseInt(this.settingsForm.value['grafana_port']),
      "company_name": this.settingsForm.value['company_name']
    }
    this.settingsService.saveSettings(value).subscribe((saveData: any) => {
      Swal.fire('Thank you...', 'Your Setting Page is updated!', 'success')
      this.getSettings();
    })

  }

  testRainbow() {
    let value = {
      company_name: this.settingsForm.value.company_name
    }
    this.settingsService.testRainbow(value).subscribe(
      (data: any) => {
        this.testConnectSucess = 'true';
      },
      (error: any) => {
        this.testConnectSucess = 'false';
      }
    );

  }

}

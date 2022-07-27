import { Injectable } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { HttpService } from "./http/http.service";
import { environment } from "src/environments/environment";
import { Settings } from "../models/settings";

@Injectable({
  providedIn: 'root'
})
export class SettingsService extends HttpService<Settings> {

  constructor(httpClient: HttpClient) {
    super(httpClient, environment.restURL, environment.settings);
  }

  getSettings() {
    return this.get();
  }

  saveSettings(settingsData: Settings) {
    return this.post(settingsData);
  }
  testRainbow(testData: any) {
    return this.testconnection(testData)
  }

}

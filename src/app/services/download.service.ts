import { Injectable } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { HttpService } from "./http/http.service";
import { DownloadFile } from "../models/download"
import { environment } from 'src/environments/environment';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class downloadService extends HttpService<downloadService>  {

  constructor(httpClient: HttpClient) {
    super(httpClient, environment.restURL, environment.download)

  }
  getDownloadFile() {
    return this.getDownload();
  }
  uploadFromOffline(file: any) {
    const fd = new FormData();
    fd.append('script', 'ddfd')
    return this.postFile(fd);
  }


  aleUpgrade() {
    return this.getAleUpgrade();
  }

}

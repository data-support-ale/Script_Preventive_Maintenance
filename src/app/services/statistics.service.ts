import { Injectable } from '@angular/core';
import { HttpClient } from "@angular/common/http";
import { Statistics } from '../models/statistics';
import { HttpService } from "./http/http.service";
import { environment } from 'src/environments/environment';


@Injectable({
  providedIn: 'root'
})
export class StatisticsService extends HttpService<Statistics> {

  constructor(httpClient: HttpClient) {
    super(httpClient, environment.restURL, environment.statistics)
  }

  getStatistics() {
    return this.get();
  }

  postDateFilter(data: any) {
    return this.postByValue(data, 'datafilter')
  }



}
import { Component, OnInit } from '@angular/core';
import { TableModule } from 'primeng/table';
import { AnyCatcher } from 'rxjs/internal/AnyCatcher';
import { FormGroup, FormControl, Validators, FormBuilder } from '@angular/forms'
import { StatisticsService } from '../services/statistics.service';
import { DateAdapter } from '@angular/material/core';
import { NgxSpinnerService } from "ngx-spinner";
@Component({
  selector: 'app-statistics',
  templateUrl: './statistics.component.html',
  styleUrls: ['./statistics.component.css']
})
export class StatisticsComponent implements OnInit {
  statistics: any[] = [];
  mainData: any[] = [];
  statisticsObject: any;
  noOfPages = '1';
  noOfPagesLength: any = 0;
  first = 0;
  minDate: any;
  maxDate = this.formatDate();
  fromDate: any = this.formatDate();
  toDate: any = this.formatDate();
  filterButton: boolean = false;
  constructor(private fb: FormBuilder,
    private spinner: NgxSpinnerService,
    private statisticsService: StatisticsService,
    private dateAdapter: DateAdapter<Date>) {
    this.dateAdapter.setLocale('en-GB'); //dd/MM/yyyy
    const min = new Date();
    min.setDate(min.getDate() - 20)
    this.minDate = this.formatDate(min);
  }
  ngOnInit(): void {
    this.spinner.show();
    this.getStatistics()
  }
  getStatistics() {
    this.statisticsService.getStatistics().subscribe((res: any) => {
      this.spinner.hide();
      if (res.Message === 'Success') {
        this.statisticsObject = res;
        this.statisticsObject = res;
        let obj = this.statisticsObject.statistics;
        let reversData = obj.reverse();
        this.mainData = reversData;
        let todayData = reversData.filter((item) => item['timestamp'].substring(0, 10) === this.toDate)
        this.statistics = todayData;
        this.noOfPagesLength = Math.ceil(this.statistics.length / 30);
      } else {
        this.statisticsObject = [];
      }
    })
  }
  counter(i: number) {
    return new Array(i);
  }
  typeCastToLower(value: string) {
    return value.toLowerCase();
  }
  onDateChange() {
    if (this.formatDate(this.fromDate) > this.formatDate(this.toDate)) {
      this.filterButton = true
      return this.filterButton;
    } else {
      this.filterButton = false;
      return this.filterButton
    }
  }
  noOfPagesChange() {
    this.first = (+this.noOfPages - 1) * 30;
  }

  paginate(event: any) {
    let pageIndex = event.first / event.rows + 1
    this.noOfPages = '' + pageIndex + '';
  }
  searchData() {
    this.getDatesInRange(this.formatDate(this.fromDate), this.formatDate(this.toDate))
  }
  getDatesInRange(startDate, endDate) {
    let data = this.mainData;
    let betweenDatesData = data.filter((item) => item['timestamp'].substring(0, 10) >= startDate && item['timestamp'].substring(0, 10) <= endDate)
    this.statistics = betweenDatesData;
    this.noOfPagesLength = Math.ceil(this.statistics.length / 30);
  }
  formatDate(date = new Date()) {
    var d = new Date(date),
      day = '' + d.getDate(),
      month = '' + (d.getMonth() + 1),
      year = '' + d.getFullYear();
    if (day.length < 2) {
      day = '0' + day
    }
    if (month.length < 2) {
      month = '0' + month;
    }
    return [year, month, day].join('-')
  }
  numberOfDays() {
    var toDate = new Date(this.toDate);
    var fromdate = new Date(this.fromDate);
    var diffDays = toDate.getDate() - fromdate.getDate();
    if (diffDays > -1) {
      return diffDays;
    } else {
      return 0;
    }
  }
}
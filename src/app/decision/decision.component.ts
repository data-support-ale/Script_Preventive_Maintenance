import { Component, OnInit, AfterViewInit, ViewChild } from "@angular/core";
import { DecisionService } from "../services/decision/decision.service";
import { Decision } from "../models/decision";
@Component({
  selector: "app-decision",
  templateUrl: "./decision.component.html",
  styleUrls: ["./decision.component.css"],
})
export class DecisionComponent implements OnInit {
  constructor(private decisionService: DecisionService) { }
  decisions: Decision[] = [];
  noOfPages = '1';
  noOfPagesLength: any = 0;
  first = 0;
  searchValue: any;

  counter(i: number) {
    return new Array(i);
  }

  noOfPagesChange() {
    this.first = (+this.noOfPages - 1) * 30;
  }
  paginate(event: any) {
    let pageIndex = event.first / event.rows + 1
    this.noOfPages = '' + pageIndex + '';
  }
  ngOnInit(): void {
    this.decisionService.get().subscribe((data: any) => {
      if (data.Message === 'Success') {
        let obj = data.Decision;
        this.decisions = obj.reverse();
        this.decisionService = data;
        this.noOfPagesLength = Math.ceil(this.decisions.length / 30);
      } else {
        this.decisions = [];
      }
    });
  }

  doFilter(event: any, table: any) {
    table.filter(event.target.value, 'ip_address', 'contains');

    console.log(table)
    // this.noOfPagesLength = Math.ceil(table.filter(event.target.value, 'ip_address', 'contains').length / 30);
  }

}

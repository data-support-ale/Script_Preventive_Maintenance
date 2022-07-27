import { AfterViewInit, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from 'src/app/services/auth.service';

@Component({
  selector: 'app-page-not-found',
  templateUrl: './page-not-found.component.html',
  styleUrls: ['./page-not-found.component.css'],
  encapsulation: ViewEncapsulation.None
})
export class PageNotFoundComponent implements OnInit, AfterViewInit {

  constructor(private http: AuthService, public router: Router) {
  }

  ngOnInit(): void {
  }

  ngAfterViewInit() {
    this.http.pageNotFound.next(true);

  }

  rulePage() {
    this.router.navigate(['/rules']);
  }

}

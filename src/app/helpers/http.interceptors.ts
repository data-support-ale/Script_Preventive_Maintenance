import { Injectable } from "@angular/core";
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
} from "@angular/common/http";
import { Observable } from "rxjs";
import { CookieService } from 'ngx-cookie';

@Injectable()
export class HeaderInterceptor implements HttpInterceptor {
 private xsrftoken:string;
  constructor(private cookieService: CookieService) {
  this.xsrftoken = this.cookieService.get('csrftoken');  
}

  intercept(
    request: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    // add auth header with jwt if account is logged in and request is to the api url
    // const account = this.accountService.accountValue;
    // const isLoggedIn = account?.token;
    // const isApiUrl = request.url.startsWith(environment.apiUrl);
    // if (isLoggedIn && isApiUrl) {
    request = request.clone({
     withCredentials: true,
      setHeaders: {
        //Authorization: `Bearer 1243`,
        //"Content-Type": "application/json",
        //"Access-Control-Allow-Origin": "*",
        //"X-CSRFToken": this.xsrftoken,
      },
    });
    //}

    return next.handle(request);
  }
}

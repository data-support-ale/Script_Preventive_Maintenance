import { Component, HostListener, OnInit, OnDestroy } from '@angular/core';
import { FormGroup, FormControl, Validators, FormBuilder } from '@angular/forms'
import { RuleService } from '../services/rules/rule.service';
import Swal from 'sweetalert2';
import {
  Router,
  NavigationStart,
  NavigationEnd,
  Event as NavigationEvent,
} from "@angular/router";
import { Idle, DEFAULT_INTERRUPTSOURCES } from '@ng-idle/core';
import { Keepalive } from '@ng-idle/keepalive';
declare var $: any;

@Component({
  selector: 'app-rules',
  templateUrl: './rules.component.html',
  styleUrls: ['./rules.component.css']
})
export class RulesComponent implements OnInit {
  selectedOption: string = 'Default';
  editForm: any;
  newRuleForm!: FormGroup;
  rules: any[] = [];
  noOfPages = '1';
  noOfPagesLength: any = 0;
  ruleFilter: string = 'Default';
  first = 0;
  // selected
  checkedRowsList: any = []
  rulesObject: any;
  enableRuleData: any;
  selectedRuleIds: any = [];
  isAdmin: string = localStorage.getItem("isAdmin") || '';

  addRule: boolean = false;
  // noOfPages = '1';
  idleState = 'Not started.';
  timer: any;
  timedOut = false;
  lastPing?: Date = null;
  constructor(private fb: FormBuilder, private ruleService: RuleService, public router: Router, private idle: Idle,
    private keepalives: Keepalive) {
    this.editForm = this.fb.group({
      rule_name: new FormControl('', Validators.required),
      rule_id: new FormControl('', Validators.required),
      action: new FormControl('', Validators.required),
      description: new FormControl('', Validators.required)
    })
    this.ruleModel();
  }

  ruleModel() {
    this.newRuleForm = this.fb.group({
      rule_name: new FormControl('if $msg contains', Validators.required),
      action: new FormControl('', Validators.required),
      description: new FormControl('', Validators.required)
    })
  }

  ngOnInit(): void {
    this.checkIdle();
    this.getRules('Default');
  }


  getRules(rule_type: string) {
    this.ruleService.getRules().subscribe((res: any) => {
      this.rulesObject = res;
      this.selectedOption = rule_type;
      this.changeRuleType(rule_type)
    })
  }

  changeRuleType(event: any) {
    let index = this.rulesObject.data.findIndex((x: any) => x.rule_type == event);
    if (parseInt(index) > -1) {
      this.rules = this.rulesObject.data[index].rules;
      this.noOfPages = '1';
      this.noOfPagesLength = 0;
      this.first = 0;
      for (let i = 0; i < this.rules.length; i++) {
        this.rules[i].selected = false;
      }
      this.noOfPagesLength = Math.ceil(this.rules.length / 30);
      this.checkedRowsList = [];
      this.selectedRuleIds = [];
    } else {
      this.rules = [];
    }
  }

  trimMethodForDescription(description) {
    let length = 100;
    return description.length > length ?
      description.substring(0, length - 3) + "..." :
      description;
  }


  openViewActionModel() {
    $("#viewActionModal").modal('show');
  }
  openEnableModel(enable: any, rule: any) {
    this.ruleFilter = rule.rule_type;
    this.enableRuleData = {
      rule_id: this.selectedRuleIds,
      enabled: enable
    }
    $("#enableModal").modal('show');
  }
  openEditRuleModal(rule: any) {
    let value = {
      rule_name: this.checkedRowsList[0].rule_name,
      rule_id: rule.rule_id,
      action: rule.action,
      description: rule.description
    }
    this.editForm.setValue(value);
    $("#editModel").modal('show');
  }

  openDeleteRuleModal(rule: any): void {
    $("#deleteModel").modal('show');
  }

  counter(i: number) {
    return new Array(i);
  }

  noOfPagesChange() {
    this.first = (+this.noOfPages - 1) * 30;
  }

  // edit rule  api
  checkRow(rule: any, event: any, rowIndex: any) {
    if (event.checked) {
      this.checkedRowsList.push(rule);
      this.selectedRuleIds.push(rule.rules_id);
      this.rules[rowIndex].selected = true;
    } else {
      let index = this.checkedRowsList.findIndex((x: any) => x.rule_id == rule.rule_id);
      this.checkedRowsList.splice(index, 1);
      this.selectedRuleIds.splice(index, 1);
      this.rules[rowIndex].selected = false;
    }
  }

  selectAll(event: any) {
    if (event.checked) {
      this.checkedRowsList = [];
      this.selectedRuleIds = [];
      this.checkedRowsList = JSON.parse(JSON.stringify(this.rules));
      for (let i = 0; i < this.rules.length; i++) {

        this.selectedRuleIds.push(this.rules[i].rules_id)
      }
    } else {
      this.checkedRowsList = [];
      this.selectedRuleIds = [];
    }
  }

  enableRules(enable: any) {
    if (!this.selectedRuleIds.length) {
      $("#hintModal").modal('show');
      return;
    }
    this.openEnableModel(enable, this.selectedRuleIds);
  }

  openEditModal() {
    $("#editModel").modal('show');
  }

  // open add rule Modal
  openAddRuleModal(flag: any) {
    this.addRule = flag;
    this.ruleModel();
    if (this.addRule || (!this.addRule && this.checkedRowsList.length)) {
      if (this.selectedRuleIds.length < 2 || flag) {
        if (!this.addRule) {
          let value = {
            rule_name: this.checkedRowsList[0].rule_name,
            rule_id: this.checkedRowsList[0].rules_id,
            action: this.checkedRowsList[0].action,
            description: this.checkedRowsList[0].rule_description
          }
          this.newRuleForm.patchValue(value)
        }
        $("#addRuleModel").modal('show');
      } else {
        if (!flag) {
          Swal.fire('Please select only one rule')
        }
      }

    }
  }
  checkIdle() {
    // sets an idle timeout of 5 seconds, for testing purposes.
    this.idle.setIdle(1500);
    // sets a timeout period of 5 seconds. after 10 seconds of inactivity, the user will be considered timed out.
    this.idle.setTimeout(30);
    // sets the default interrupts, in this case, things like clicks, scrolls, touches to the document
    this.idle.setInterrupts(DEFAULT_INTERRUPTSOURCES);

    this.idle.onIdleEnd.subscribe(() => {
      this.idleState = 'No longer idle.'
      this.reset();
    });

    this.idle.onTimeout.subscribe(() => {
      this.idleState = 'Timed out!';
      this.timedOut = true;
      this.idle.stop();
      Swal.close();
      this.idleLogout();
    });

    this.idle.onIdleStart.subscribe(() => {
      this.idleState = 'You\'ve gone idle!'

      Swal.fire({
        title: 'You have been Idle for 25mins',
        text: 'You will be logged out in 30 secs',
        showDenyButton: true,
        showCancelButton: false,
        confirmButtonText: 'Logout',
        confirmButtonColor: '#3085d6',
        denyButtonText: `Stay Back`,
        denyButtonColor: '#6b489d'
      }).then((result) => {
        /* Read more about isConfirmed, isDenied below */
        if (result.isConfirmed) {
          this.idleLogout();
        } else if (result.isDenied) {
          this.router.navigate(['/' + this.router.url]);
          Swal.close();
          this.reset();
        }
      })
    });

    this.idle.onTimeoutWarning.subscribe((countdown) => {
      this.idleState = 'You will time out in ' + countdown + ' seconds!'
      this.timer = countdown;
    });

    // sets the ping interval to 15 seconds
    this.keepalives.interval(1500);

    this.keepalives.onPing.subscribe(() => this.lastPing = new Date());
    this.reset();
  }
  idleLogout() {
    this.router.navigate(["/logout"], { state: { flag: true } })
  }

  reset() {
    this.idle.watch();
    this.idleState = 'Started.';
    this.timedOut = false;
  }
  paginate(event: any) {
    let pageIndex = event.first / event.rows + 1
    this.noOfPages = '' + pageIndex + '';
  }

  // add new rule
  createRule(): any {
    if (!this.newRuleForm.value.rule_name.startsWith('if $msg contains')) {
      Swal.fire('"If $msg (the statement)" missing at beginning.')
      return false;
    }
    if (!this.addRule) {
      this.editRule();
      return false;
    }
    this.ruleService.addRule(this.newRuleForm.value).subscribe((rule: any) => {
      Swal.fire({
        icon: 'success',
        title: 'Great',
        text: 'Custom Rule created Successfully'
      })
      this.newRuleForm.reset();
      this.getRules('Custom');
      $("#addRuleModel").modal('hide');
    })
  }

  editRule() {
    this.ruleService.editRule(this.checkedRowsList[0].rules_id, this.newRuleForm.value).subscribe((rule: any) => {
      Swal.fire({
        icon: 'success',
        title: 'Great',
        text: 'The custom rule details are updated successfully'
      })
      this.newRuleForm.reset();
      this.getRules('Custom');
      $("#addRuleModel").modal('hide');
    })
  }

  openDeleteModal() {
    if (this.checkedRowsList.length) {
      if (this.selectedRuleIds.length < 2) {
        $("#deleteModel").modal('show');
      } else {
        Swal.fire('Please select only one rule')
      }
    }
  }

  //delete rule api
  deleteRule() {
    let ruleId = this.checkedRowsList[0].rules_id;
    this.ruleService.deleteRule(ruleId).subscribe((rule: any) => {
      this.getRules('Custom');
      // $("#deletesuccessModel").modal('show');
      Swal.fire({
        icon: 'success',
        title: 'Great',
        text: 'The selected custom rule has been deleted successfully'
      })
    }, (error: any) => {
      $("#deletefailuerModel").modal('show');
    })
  }

  enableSingleRule(rule: any, enableRuleData: any) {
    this.ruleFilter = rule[0].rule_type;
    let enabledLabel = enableRuleData?.enabled ? 'enabled' : 'disabled';
    this.ruleService.enableRules(this.selectedRuleIds, this.enableRuleData).subscribe((rule: any) => {
      Swal.fire({
        icon: 'success',
        title: 'Great',
        text: `The selected records are ${enabledLabel}`
      })
      $("#enableModal").modal('hide');
      this.getRules(this.ruleFilter);
    })
  }

}
